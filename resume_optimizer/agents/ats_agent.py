"""Agent for checking ATS compatibility of resumes."""

import re
from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.text_utils import extract_score_from_text, extract_feedback_from_text


class ATSCompatibilityAgent(BaseOptimizerAgent):
    """Agent for checking ATS compatibility of resumes."""
    
    def __init__(self, model=None):
        """Initialize the ATS compatibility agent.
        
        Args:
            model: Optional model to use
        """
        super().__init__(
            role_name="ATS Compatibility Expert",
            system_message_content=(
                "You are an expert at evaluating resumes for ATS compatibility with over 10 years of experience in resume optimization. "
                "You provide detailed feedback on how to improve a resume to better pass ATS systems. "
                "You evaluate the resume against a specific job description and provide a score out of 100 "
                "along with detailed, specific feedback for improvements. "
                "You understand ATS algorithms and keyword matching techniques used by modern recruiting software."
            ),
            model=model
        )
    
    def optimize(self, content, context):
        """Not used for the ATS agent.
        
        This method is implemented to satisfy the abstract base class.
        
        Args:
            content: Not used
            context: Not used
            
        Returns:
            None
        """
        raise NotImplementedError("ATS agent does not implement optimize method. Use check_compatibility instead.")
    
    def check_compatibility(self, resume_content, job_description):
        """Check ATS compatibility of a resume against a job description.
        
        Args:
            resume_content: The full resume content
            job_description: The job description to check against
            
        Returns:
            Tuple of (score, feedback) where score is an integer 0-100
            and feedback is a string with improvement suggestions
        """
        evaluation_message = (
            f"Evaluate this resume for ATS compatibility with the following job description:\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"RESUME:\n{resume_content}\n\n"
            f"Please provide:\n"
            f"1. A score out of 100 for ATS compatibility\n"
            f"2. Detailed feedback on how to improve the resume for better ATS performance, including:\n"
            f"   - Missing keywords that should be added\n"
            f"   - Sections that could be further optimized\n"
            f"   - Formatting suggestions for better ATS parsing\n"
            f"   - Overall assessment of how well the resume matches the job description"
        )
        
        # Get the response and extract the score and feedback
        response = self.process(evaluation_message)
        
        # Extract score and feedback
        score = extract_score_from_text(response, default=75)
        feedback = extract_feedback_from_text(response)
        
        return score, feedback