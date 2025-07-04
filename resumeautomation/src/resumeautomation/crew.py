from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os
import sys
from pathlib import Path

# Add tools to path
current_dir = Path(__file__).parent
tools_dir = current_dir / "tools"
sys.path.insert(0, str(tools_dir))

# Import custom tools
from google_sheets_tool import GoogleSheetsTool
from google_drive_tool import GoogleDriveTool
from pdf_analysis_tool import PDFAnalysisTool
from latex_tool import LaTeXTool

@CrewBase
class ResumeAutomation():
    """Resume Automation Crew - Complete workflow for generating customized resumes"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew with all necessary tools."""
        self.sheets_tool = GoogleSheetsTool()
        self.drive_tool = GoogleDriveTool()
        self.pdf_tool = PDFAnalysisTool()
        self.latex_tool = LaTeXTool()

    @agent
    def sheet_monitor(self) -> Agent:
        """Agent responsible for monitoring Google Sheets for new requests."""
        return Agent(
            config=self.agents_config['sheet_monitor'],
            tools=[self.sheets_tool],
            verbose=True,
            memory=True,
            max_iter=5,
            allow_delegation=False
        )

    @agent
    def base_resume_analyzer(self) -> Agent:
        """Agent responsible for analyzing base resume templates."""
        return Agent(
            config=self.agents_config['base_resume_analyzer'],
            tools=[self.drive_tool, self.pdf_tool],
            verbose=True,
            memory=True,
            max_iter=5,
            allow_delegation=False
        )

    @agent
    def latex_generator(self) -> Agent:
        """Agent responsible for generating customized LaTeX resumes."""
        return Agent(
            config=self.agents_config['latex_generator'],
            tools=[self.latex_tool, self.drive_tool],
            verbose=True,
            memory=True,
            max_iter=7,
            allow_delegation=False
        )

    @agent
    def pdf_validator(self) -> Agent:
        """Agent responsible for PDF validation and quality checking."""
        return Agent(
            config=self.agents_config['pdf_validator'],
            tools=[self.pdf_tool],
            verbose=True,
            memory=True,
            max_iter=5,
            allow_delegation=False
        )

    @agent
    def optimization_specialist(self) -> Agent:
        """Agent responsible for optimizing resumes to meet requirements."""
        return Agent(
            config=self.agents_config['optimization_specialist'],
            tools=[self.latex_tool, self.pdf_tool],
            verbose=True,
            memory=True,
            max_iter=10,
            allow_delegation=False
        )

    @agent
    def workflow_coordinator(self) -> Agent:
        """Agent responsible for coordinating the entire workflow."""
        return Agent(
            config=self.agents_config['workflow_coordinator'],
            tools=[self.sheets_tool, self.drive_tool],
            verbose=True,
            memory=True,
            max_iter=5,
            allow_delegation=True
        )

    @task
    def monitor_new_requests(self) -> Task:
        """Task to monitor Google Sheets for new resume requests."""
        return Task(
            config=self.tasks_config['monitor_new_requests'],
            agent=self.sheet_monitor,
            async_execution=False
        )

    @task
    def analyze_base_resume(self) -> Task:
        """Task to analyze the base resume template."""
        return Task(
            config=self.tasks_config['analyze_base_resume'],
            agent=self.base_resume_analyzer,
            async_execution=True
        )

    @task
    def generate_customized_resume(self) -> Task:
        """Task to generate customized LaTeX resume."""
        return Task(
            config=self.tasks_config['generate_customized_resume'],
            agent=self.latex_generator,
            context=[self.monitor_new_requests, self.analyze_base_resume],
            async_execution=False
        )

    @task
    def compile_and_validate_pdf(self) -> Task:
        """Task to compile LaTeX and validate PDF output."""
        return Task(
            config=self.tasks_config['compile_and_validate_pdf'],
            agent=self.pdf_validator,
            context=[self.generate_customized_resume],
            async_execution=False
        )

    @task
    def optimize_if_needed(self) -> Task:
        """Task to optimize resume if it doesn't meet requirements."""
        return Task(
            config=self.tasks_config['optimize_if_needed'],
            agent=self.optimization_specialist,
            context=[self.compile_and_validate_pdf],
            async_execution=False
        )

    @task
    def finalize_and_upload(self) -> Task:
        """Task to finalize and upload completed resume."""
        return Task(
            config=self.tasks_config['finalize_and_upload'],
            agent=self.workflow_coordinator,
            context=[self.optimize_if_needed],
            async_execution=False,
            output_file='resume_generation_report.md'
        )

    @task
    def handle_errors(self) -> Task:
        """Task to handle any errors during the process."""
        return Task(
            config=self.tasks_config['handle_errors'],
            agent=self.workflow_coordinator,
            async_execution=False
        )

    @crew
    def crew(self) -> Crew:
        """Create the Resume Automation crew with all agents and tasks."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            planning=True,
            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small"
                }
            },
            max_rpm=10,
            share_crew=False
        )

    # Additional helper methods for manual operations
    def check_for_new_requests(self):
        """Manually check for new requests (for testing)."""
        try:
            result = self.sheets_tool.find_new_requests()
            return result
        except Exception as e:
            return f"Error checking requests: {str(e)}"

    def get_base_resume_templates(self):
        """Get list of available base resume templates."""
        try:
            result = self.drive_tool._run("list", "templates")
            return result
        except Exception as e:
            return f"Error listing templates: {str(e)}"

    def test_latex_compilation(self):
        """Test LaTeX compilation with sample data."""
        try:
            sample_data = {
                "name": "John Doe",
                "phone": "(555) 123-4567",
                "email": "john.doe@email.com",
                "summary": "Experienced software engineer with expertise in Python and AI.",
                "experience": [
                    {
                        "title": "Software Engineer",
                        "company": "Tech Corp",
                        "location": "San Francisco, CA",
                        "duration": "2020-Present",
                        "items": [
                            "Developed Python applications",
                            "Led AI/ML projects",
                            "Mentored junior developers"
                        ]
                    }
                ],
                "skills": {
                    "Programming": ["Python", "JavaScript", "SQL"],
                    "Technologies": ["React", "Docker", "AWS"]
                },
                "education": [
                    {
                        "institution": "University of California",
                        "degree": "BS Computer Science",
                        "location": "Berkeley, CA",
                        "graduation": "2020"
                    }
                ]
            }
            
            import json
            result = self.latex_tool._run(
                "generate", 
                "professional", 
                json.dumps(sample_data), 
                "test_resume"
            )
            return result
        except Exception as e:
            return f"Error testing LaTeX: {str(e)}"

    def validate_environment(self):
        """Validate that all required environment variables and tools are available."""
        validation_results = {
            "environment_variables": {},
            "tools": {},
            "dependencies": {}
        }
        
        # Check environment variables
        required_env_vars = [
            'OPENAI_API_KEY',
            'GOOGLE_SHEETS_ID',
            'GOOGLE_DRIVE_BASE_FOLDER',
            'GOOGLE_DRIVE_GENERATED_FOLDER',
            'GOOGLE_DRIVE_TEMPLATES_FOLDER'
        ]
        
        for var in required_env_vars:
            value = os.getenv(var)
            validation_results["environment_variables"][var] = {
                "present": bool(value),
                "value": value[:10] + "..." if value and len(value) > 10 else value
            }
        
        # Check tool availability
        try:
            self.sheets_tool._run("read", "A1:A1")
            validation_results["tools"]["google_sheets"] = "accessible"
        except Exception as e:
            validation_results["tools"]["google_sheets"] = f"error: {str(e)}"
        
        try:
            self.drive_tool._run("list", "base")
            validation_results["tools"]["google_drive"] = "accessible"
        except Exception as e:
            validation_results["tools"]["google_drive"] = f"error: {str(e)}"
        
        # Check LaTeX availability
        try:
            import subprocess
            subprocess.run(['pdflatex', '--version'], capture_output=True, check=True)
            validation_results["dependencies"]["pdflatex"] = "available"
        except Exception:
            validation_results["dependencies"]["pdflatex"] = "not available"
        
        return validation_results