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
        return self.coordinator.optimize_resume(
            resume_path=resume_path,
            job_description=job_description,
            output_path=output_path
        )