# resume_optimizer/core/workforce_optimizer.py
from resume_optimizer.workforce.workflow import ResumeWorkflow
from typing import Dict, Any

class WorkforceResumeOptimizer:
    """CAMEL Workforce-powered resume optimizer."""
    
    def __init__(self, resume_path, job_description, output_path="optimized_resume.tex", model=None, debug_mode=True):
        """Initialize the workforce resume optimizer.
        
        Args:
            resume_path: Path to the LaTeX resume file
            job_description: Job description text
            output_path: Path where the optimized resume will be saved
            model: Optional model to use for agents
            debug_mode: Whether to print debug information
        """
        self.resume_path = resume_path
        self.job_description = job_description
        self.output_path = output_path
        self.model = model
        self.debug_mode = debug_mode
        
        # Initialize the workforce workflow
        self.workflow = ResumeWorkflow(model=model)
    
    def run(self) -> Dict[str, Any]:
        """Run the resume optimization process using the workforce.
        
        Returns:
            Dictionary with optimization results
        """
        print("🚀 Starting Resume Optimization with CAMEL Workforce...")
        
        # Run the optimization workflow
        results = self.workflow.optimize_resume(
            resume_path=self.resume_path,
            job_description=self.job_description,
            output_path=self.output_path
        )
        
        print(f"✅ Resume optimization complete! ATS Score: {results.get('ats_score', 'N/A')}/100")
        print(f"📄 Optimized resume saved to {self.output_path}")
        
        return results