# resume_optimizer/tasks/task_definitions.py
from camel.tasks import Task
from pathlib import Path
from typing import Dict, List, Optional, Union

class ResumeTask(Task):
    """Extended Task class for resume optimization tasks."""
    
    def __init__(
        self, 
        content: str, 
        id: str, 
        resume_path: Optional[Union[str, Path]] = None,
        job_description: Optional[str] = None,
        section_name: Optional[str] = None,
        section_content: Optional[str] = None,
        analysis_results: Optional[Dict] = None,
        dependencies: Optional[List[str]] = None
    ):
        """Initialize a resume task with resume-specific metadata."""
        super().__init__(content=content, id=id)
        self.resume_path = Path(resume_path) if resume_path else None
        self.job_description = job_description
        self.section_name = section_name
        self.section_content = section_content
        self.analysis_results = analysis_results or {}
        self.dependencies = dependencies or []

def create_analyze_job_task(job_description: str, task_id: str = "analyze_job") -> ResumeTask:
    """Create a job analysis task."""
    return ResumeTask(
        content="Analyze job description to extract skills, requirements, and keywords",
        id=task_id,
        job_description=job_description
    )

def create_extract_sections_task(resume_path: str, task_id: str = "extract_sections") -> ResumeTask:
    """Create a section extraction task."""
    return ResumeTask(
        content="Extract sections from the resume",
        id=task_id,
        resume_path=resume_path
    )

def create_optimize_section_task(
    section_name: str, 
    section_content: str, 
    analysis_results: Dict, 
    task_id: str
) -> ResumeTask:
    """Create a section optimization task."""
    return ResumeTask(
        content=f"Optimize the {section_name} section based on job analysis",
        id=task_id,
        section_name=section_name,
        section_content=section_content,
        analysis_results=analysis_results,
        dependencies=["analyze_job"]
    )

def create_evaluate_task(
    original_content: str, 
    optimized_content: str, 
    analysis_results: Dict, 
    task_id: str
) -> ResumeTask:
    """Create an evaluation task."""
    return ResumeTask(
        content="Evaluate the optimized resume against job requirements",
        id=task_id,
        section_content=original_content,
        analysis_results=analysis_results
    )

def create_assemble_resume_task(
    resume_path: str, 
    optimized_sections: Dict[str, str], 
    task_id: str = "assemble_resume"
) -> ResumeTask:
    """Create a task to assemble optimized sections into a complete resume."""
    return ResumeTask(
        content="Assemble optimized sections into a complete resume",
        id=task_id,
        resume_path=resume_path,
        # Store optimized sections in the analysis_results field temporarily
        analysis_results={"optimized_sections": optimized_sections}
    )