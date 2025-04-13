"""ResumeForgeAI: CAMEL-powered resume optimization package."""

__version__ = "0.2.0"

# Import core components for easy access
from resume_optimizer.core.workforce_optimizer import WorkforceResumeOptimizer
from resume_optimizer.core.latex_handler import LatexHandler
from resume_optimizer.utils.resume_evaluator import ResumeEvaluator
from resume_optimizer.core.job_analyzer import JobAnalyzer

# Import CAMEL components for easy access
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.societies.workforce import Workforce
from camel.tasks import Task

# Import utility functions for easy access
from resume_optimizer.utils.model_factory import create_default_model, get_model_by_name

# Define the main optimization function
def optimize_resume(
    resume_path, 
    job_description_path, 
    output_path="optimized_resume.tex", 
    model=None, 
    debug_mode=True,
    verbose=True,
    sections=None,
    iterations=2
):
    """Optimize a resume for a specific job description.
    
    Args:
        resume_path: Path to the LaTeX resume file
        job_description_path: Path to the job description file
        output_path: Path where the optimized resume will be saved
        model: Optional model to use for agents
        debug_mode: Whether to save debug information and files
        verbose: Whether to print detailed output
        sections: List of specific sections to optimize (default: all relevant sections)
        iterations: Number of optimization iterations to perform
        
    Returns:
        Dictionary with optimization results
    """
    # Read job description
    with open(job_description_path, 'r') as f:
        job_description = f.read()
    
    # Create and run the optimizer
    optimizer = WorkforceResumeOptimizer(
        resume_path=resume_path,
        job_description=job_description,
        output_path=output_path,
        model=model,
        debug_mode=debug_mode,
        verbose=verbose,
        sections_to_optimize=sections,
        optimization_iterations=iterations
    )
    
    # Run optimization and return results
    return optimizer.run()