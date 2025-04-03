"""Agent for evaluating resume section optimizations."""

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.text_utils import format_analysis_for_prompt


class EvaluatorAgent(BaseOptimizerAgent):
    """Agent for evaluating optimized resume sections."""
    
    def __init__(self, model=None):
        """Initialize the evaluator agent.
        
        Args:
            model: Optional model to use
        """
        super().__init__(
            role_name="Resume Optimization Evaluator",
            system_message_content=(
                "You are an expert at evaluating resume optimizations. You can compare "
                "an optimized resume section against the original and the job description analysis "
                "to identify missed opportunities and areas for improvement. Your feedback is specific, "
                "actionable, and focused on maximizing ATS compatibility and human appeal."
            ),
            model=model
        )
    
    def optimize(self, content, context):
        """Not used for the evaluator agent.
        
        This method is implemented to satisfy the abstract base class.
        
        Args:
            content: Not used
            context: Not used
            
        Returns:
            None
        """
        raise NotImplementedError("Evaluator agent does not implement optimize method. Use evaluate_section instead.")
    
    def evaluate_section(self, section_type, original_section, optimized_section, analysis_results):
        """Evaluate optimization and provide feedback for improvement.
        
        Args:
            section_type: Type of section ("skills" or "experience")
            original_section: Original section content
            optimized_section: Optimized section content
            analysis_results: Job description analysis results
            
        Returns:
            Evaluation feedback as string
        """
        # Create specific criteria based on section type
        if section_type == "skills":
            criteria = (
                "1. Inclusion of all hard skills from the analysis\n"
                "2. Appropriate organization of skills into categories\n"
                "3. Prioritization of required skills\n"
                "4. Removal of irrelevant skills\n"
                "5. Proper terminology matching with the job description"
            )
        else:  # experience
            criteria = (
                "1. Use of all keywords from job descrptioninto the customized resume's work experience section bullet points\n"
                "2. Incorporation of both hard and soft skills\n"
                "3. Use of strong action verbs\n"
                "4. Quantifiable achievements and metrics\n"
                "5. Relevance of highlighted experiences to job requirements"
            )
        
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(analysis_results)
        
        evaluation_prompt = (
            f"Evaluate this optimized {section_type} section against the job description analysis:\n\n"
            f"JOB ANALYSIS:\n{job_analysis_text}\n\n"
            f"ORIGINAL SECTION:\n{original_section}\n\n"
            f"OPTIMIZED SECTION:\n{optimized_section}\n\n"
            f"Evaluate against these criteria:\n{criteria}\n\n"
            f"Please provide:\n"
            f"1. An overall assessment (1-10)\n"
            f"2. Specific missed opportunities\n"
            f"3. Detailed suggestions for improvement\n"
            f"4. Any keywords or skills that should be added\n"
            f"5. Any content that should be rephrased or removed"
        )
        
        response = self.process(evaluation_prompt)
        
        print(f"\n✅ {section_type.capitalize()} Section Evaluation Complete")
        
        return response