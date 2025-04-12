# resume_optimizer/workforce/coordinator.py
from camel.societies.workforce import Workforce
from camel.tasks import Task
from typing import Dict, List, Optional, Any

class ResumeWorkforceCoordinator:
    """Coordinator for the resume optimization workforce."""
    
    def __init__(self, workforce_name: str = "Resume Optimization Workforce"):
        """Initialize the workforce coordinator."""
        self.workforce = Workforce(workforce_name)
        self.results_cache = {}
    
    def add_worker(self, description: str, worker_agent):
        """Add a worker to the workforce."""
        self.workforce.add_single_agent_worker(description, worker=worker_agent)
        return self
    
    def process_task(self, task: Task) -> Task:
        """Process a task using the workforce."""
        return self.workforce.process_task(task)
    
    def optimize_resume(self, 
                       resume_path: str, 
                       job_description: str, 
                       output_path: str) -> Dict[str, Any]:
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
        analyze_result = self.process_task(analyze_task)
        analysis_data = parse_task_result(analyze_result)
        
        # Step 2: Extract sections from resume
        extract_task = create_extract_sections_task(resume_path)
        extract_result = self.process_task(extract_task)
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
            section_tasks[section_name] = section_task
        
        # Process each section task
        for section_name, task in section_tasks.items():
            result = self.process_task(task)
            result_data = parse_task_result(result)
            optimized_sections[section_name] = result_data.get("optimized_content", 
                                                              result_data.get("result", ""))
        
        # Step 4: Assemble the optimized resume
        assemble_task = create_assemble_resume_task(
            resume_path=resume_path,
            optimized_sections=optimized_sections
        )
        assemble_result = self.process_task(assemble_task)
        
        # Save the optimized resume
        latex_handler.save_resume(assemble_result.result, output_path)
        
        # Step 5: Check ATS compatibility
        ats_task = Task(
            content="Check ATS compatibility of the optimized resume",
            id="check_ats_compatibility"
        )
        ats_task.resume_path = output_path
        ats_task.job_description = job_description
        
        ats_result = self.process_task(ats_task)
        ats_data = parse_task_result(ats_result)
        
        return {
            "ats_score": ats_data.get("score", 0),
            "ats_feedback": ats_data.get("feedback", ""),
            "optimized_sections": optimized_sections,
            "analysis": analysis_data
        }