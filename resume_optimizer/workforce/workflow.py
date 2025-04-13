# resume_optimizer/workforce/workflow.py
from camel.societies.workforce import Workforce
from resume_optimizer.workforce.workers import (
    JobAnalysisWorker,
    SectionExtractorWorker,
    SkillsOptimizationWorker,
    ExperienceOptimizationWorker,
    SummaryOptimizationWorker,
    ResumeAssemblerWorker,
    ATSCheckWorker
)
from resume_optimizer.workforce.coordinator import ResumeWorkforceCoordinator
from resume_optimizer.utils.model_factory import create_default_model

class ResumeWorkflow:
    """Workflow for resume optimization using CAMEL's Workforce."""
    
    def __init__(self, model=None):
        """Initialize the resume workflow.
        
        Args:
            model: Optional model to use for all agents
        """
        self.model = model if model else create_default_model()
        self.coordinator = self._setup_workforce()
    
    def _setup_workforce(self):
        """Set up the resume optimization workforce."""
        coordinator = ResumeWorkforceCoordinator()
        
        # Add workers
        coordinator.add_worker(
            "Analyzes job descriptions and extracts key requirements, skills, and keywords",
            JobAnalysisWorker(model=self.model)
        )
        
        coordinator.add_worker(
            "Extracts and identifies different sections from LaTeX resumes",
            SectionExtractorWorker(model=self.model)
        )
        
        coordinator.add_worker(
            "Optimizes technical skills sections to match job requirements",
            SkillsOptimizationWorker(model=self.model)
        )
        
        coordinator.add_worker(
            "Enhances work experience sections to highlight relevant achievements",
            ExperienceOptimizationWorker(model=self.model)
        )
        
        coordinator.add_worker(
            "Creates powerful professional summaries aligned with job requirements",
            SummaryOptimizationWorker(model=self.model)
        )
        
        coordinator.add_worker(
            "Assembles optimized sections into a complete resume",
            ResumeAssemblerWorker(model=self.model)
        )
        
        coordinator.add_worker(
            "Evaluates ATS compatibility and provides detailed feedback",
            ATSCheckWorker(model=self.model)
        )
        
        return coordinator
    
    def optimize_resume(self, resume_path, job_description, output_path):
        """Optimize a resume using the workforce.
        
        Args:
            resume_path: Path to the resume file
            job_description: Job description text
            output_path: Path to save the optimized resume
            
        Returns:
            Dictionary with optimization results
        """
        from resume_optimizer.tasks.task_definitions import (
            create_analyze_job_task,
            create_extract_sections_task,
            create_optimize_section_task,
            create_assemble_resume_task
        )
        from resume_optimizer.tasks.task_utils import parse_task_result
        from resume_optimizer.core.latex_handler import LatexHandler
        
        latex_handler = LatexHandler()
        
        # Step 1: Analyze job description
        analyze_task = create_analyze_job_task(job_description)
        analyze_task.additional_info = {"job_description": job_description}  # Store in additional_info
        analyze_result = self.coordinator.process_task(analyze_task)
        analysis_data = parse_task_result(analyze_result)
        
        # Step 2: Extract sections from resume
        extract_task = create_extract_sections_task(resume_path)
        extract_result = self.coordinator.process_task(extract_task)
        sections_data = parse_task_result(extract_result)
        
        # Step 3: Optimize each section in parallel
        section_tasks = {}
        optimized_sections = {}
        
        for section_name, section_content in sections_data.get("sections", {}).items():
            task_id = f"optimize_{section_name.lower().replace(' ', '_')}"
            section_task = create_optimize_section_task(
                section_name=section_name,
                section_content=section_content,
                analysis_results=analysis_data,
                task_id=task_id
            )
            section_task.additional_info = {"analysis_results": analysis_data}  # Store in additional_info
            section_tasks[section_name] = section_task
        
        # Process each section task
        for section_name, task in section_tasks.items():
            result = self.coordinator.process_task(task)
            result_data = parse_task_result(result)
            optimized_sections[section_name] = result_data.get("optimized_content", 
                                                              result_data.get("result", ""))
        
        # Step 4: Assemble the optimized resume
        assemble_task = create_assemble_resume_task(
            resume_path=resume_path,
            optimized_sections=optimized_sections
        )
        assemble_task.additional_info = {"optimized_sections": optimized_sections}  # Store in additional_info
        assemble_result = self.coordinator.process_task(assemble_task)
        
        # Save the optimized resume
        latex_handler.save_resume(assemble_result.result, output_path)
        
        # Step 5: Check ATS compatibility
        ats_task = Task(
            content="Check ATS compatibility of the optimized resume",
            id="check_ats_compatibility"
        )
        ats_task.additional_info = {
            "resume_path": output_path,
            "job_description": job_description
        }  # Store in additional_info
        ats_result = self.coordinator.process_task(ats_task)
        ats_data = parse_task_result(ats_result)
        
        return {
            "ats_score": ats_data.get("score", 0),
            "ats_feedback": ats_data.get("feedback", ""),
            "optimized_sections": optimized_sections,
            "analysis": analysis_data
        }