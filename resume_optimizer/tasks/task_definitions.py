# resume_optimizer/tasks/task_definitions.py
from camel.tasks import Task
from pathlib import Path
from typing import Dict, List, Optional, Union

# Task metadata registry to store additional data
task_metadata = {}

def create_analyze_job_task(job_description: str, task_id: str = "analyze_job") -> Task:
    """Create a job analysis task."""
    task = Task(
        content="Analyze job description to extract skills, requirements, and keywords",
        id=task_id,
    )
    # Store job description in metadata registry
    task_metadata[task_id] = {"job_description": job_description}
    return task

def create_extract_sections_task(resume_path: str, task_id: str = "extract_sections") -> Task:
    """Create a section extraction task."""
    task = Task(
        content="Extract sections from the resume",
        id=task_id,
    )
    task_metadata[task_id] = {"resume_path": resume_path}
    return task

def create_optimize_section_task(
    section_name: str, 
    section_content: str, 
    analysis_results: Dict, 
    task_id: str
) -> Task:
    """Create a section optimization task."""
    task = Task(
        content=f"Optimize the {section_name} section based on job analysis",
        id=task_id,
    )
    task_metadata[task_id] = {
        "section_name": section_name,
        "section_content": section_content,
        "analysis_results": analysis_results,
        "dependencies": ["analyze_job"]
    }
    return task

def create_evaluate_task(
    original_content: str, 
    optimized_content: str, 
    analysis_results: Dict, 
    task_id: str
) -> Task:
    """Create an evaluation task."""
    task = Task(
        content="Evaluate the optimized resume against job requirements",
        id=task_id,
    )
    task_metadata[task_id] = {
        "section_content": original_content,
        "optimized_content": optimized_content,
        "analysis_results": analysis_results
    }
    return task

def create_assemble_resume_task(
    resume_path: str, 
    optimized_sections: Dict[str, str], 
    task_id: str = "assemble_resume"
) -> Task:
    """Create a task to assemble optimized sections into a complete resume."""
    task = Task(
        content="Assemble optimized sections into a complete resume",
        id=task_id,
    )
    task_metadata[task_id] = {
        "resume_path": resume_path,
        "optimized_sections": optimized_sections
    }
    return task

def create_ats_check_task(
    resume_path: str,
    job_description: str,
    task_id: str = "check_ats_compatibility"
) -> Task:
    """Create a task to check ATS compatibility."""
    task = Task(
        content="Check ATS compatibility of the optimized resume",
        id=task_id,
    )
    task_metadata[task_id] = {
        "resume_path": resume_path,
        "job_description": job_description
    }
    return task

def get_task_metadata(task_id: str) -> Dict:
    """Get metadata for a task."""
    return task_metadata.get(task_id, {})