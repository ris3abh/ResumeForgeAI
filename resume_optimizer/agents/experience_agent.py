"""Agent for optimizing the work experience section of a resume."""

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.latex_utils import extract_latex_content
from resume_optimizer.utils.text_utils import format_analysis_for_prompt


class ExperienceOptimizerAgent(BaseOptimizerAgent):
    """Agent for optimizing the work experience section of a resume."""
    
    def __init__(self, model=None):
        """Initialize the experience optimizer agent.
        
        Args:
            model: Optional model to use
        """
        super().__init__(
            role_name="Work Experience Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing work experience sections to perfectly match job descriptions. "
                "You know how to incorporate keywords, hard skills, soft skills, and action words while maintaining "
                "the original format and integrity of accomplishments by 30 perecent, "
                "feel free to add or remove bullet existing bullet points if they are not a good alignment with the job descripton or analysis."
            ),
            model=model
        )
        
        # List of strong action verbs for resume bullets
        self.action_words = [
            "Spearheaded", "Orchestrated", "Revolutionized", "Implemented", "Pioneered", 
            "Transformed", "Streamlined", "Catalyzed", "Overhauled", "Innovated", 
            "Leveraged", "Optimized", "Negotiated", "Cultivated", "Accelerated", 
            "Championed", "Executed", "Launched", "Redesigned", "Maximized", 
            "Engineered", "Strategized", "Revitalized", "Conceptualized", "Facilitated", 
            "Generated", "Amplified", "Consolidated", "Instituted", "Reengineered", 
            "Mobilized", "Formulated", "Mentored", "Synthesized", "Drove", 
            "Propelled", "Reconciled", "Galvanized", "Expedited"
        ]
    
    def optimize(self, experience_section, jd_analysis):
        """Optimize the work experience section based on job description analysis.
        
        Args:
            experience_section: The original work experience section content
            jd_analysis: The job description analysis results
            
        Returns:
            Optimized work experience section content
        """
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(jd_analysis)
        action_words_text = ", ".join(self.action_words)
        
        # Create the specialized prompt for experience optimization
        experience_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Work Experience Section: \n\n<Resume Work Experience Section Start>\n{experience_section}\n<Resume Work Experience Section End>\n\n"
            f"I would like you to make the work experience section well-tailored to incorporate the keywords, hard skills, and soft skills from the job analysis. "
            f"Making the Work Experience section completely tailored for the job I want to apply to.\n\n"
            f"Action Words List: {action_words_text}\n\n"
            f"Each bullet should start with one of the unique strong Actions Verb from the above list, should not contain any superfluous filler words"
            f"Make sure that the bullet points are 16-18 words long but they should be of considerable length.\n"
            f"Use strong and unique action verbs to start the sentence and include some good metrics to showcase results.\n\n"
            f"IMPORTANT: Give the updated experience section in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or AI assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current experience section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(experience_prompt)
        optimized_experience = extract_latex_content(response)
        
        # If we couldn't extract valid content, try one more time with clearer instructions
        if not optimized_experience.startswith('\\resume'):
            clarification_message = (
                "Your response wasn't formatted correctly. I need ONLY raw LaTeX code "
                "starting with \\resumeSubHeadingListStart and ending with \\resumeSubHeadingListEnd. "
                "No explanation, no markdown formatting, just the raw LaTeX content like in the original. "
                "Please try again with ONLY the LaTeX code."
            )
            response = self.process(clarification_message)
            optimized_experience = extract_latex_content(response)
            
        # Final validation to ensure we have valid LaTeX
        if not optimized_experience.startswith('\\resume'):
            print(f"Warning: Failed to generate valid LaTeX for experience section. Using original content.")
            return experience_section
        
        return optimized_experience
    
    def refine_with_feedback(self, initial_optimization, feedback, jd_analysis):
        """Refine the optimized experience section based on feedback.
        
        Args:
            initial_optimization: The initial optimized experience section
            feedback: Feedback on the initial optimization
            jd_analysis: The job description analysis
            
        Returns:
            Refined experience section content
        """
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(jd_analysis)
        
        feedback_prompt = (
            f"Refine this experience section based on the evaluation feedback:\n\n"
            f"JOB ANALYSIS:\n{job_analysis_text}\n\n"
            f"CURRENT SECTION:\n{initial_optimization}\n\n"
            f"FEEDBACK:\n{feedback}\n\n"
            f"Please incorporate the feedback to improve this section. "
            f"Make sure to address all missed opportunities and suggestions while maintaining "
            f"the proper LaTeX format. Return ONLY the improved LaTeX code."
        )
        
        response = self.process(feedback_prompt)
        refined_section = extract_latex_content(response)
        
        # If extraction failed, try clarification
        if not refined_section.startswith('\\resume'):
            clarification_message = (
                "Your response wasn't formatted correctly. I need ONLY raw LaTeX code "
                "starting with \\resumeSubHeadingListStart and ending with \\resumeSubHeadingListEnd. "
                "No explanation, no markdown formatting, just the raw LaTeX content like in the original. "
                "Please try again with ONLY the LaTeX code."
            )
            response = self.process(clarification_message)
            refined_section = extract_latex_content(response)
        
        # Final fallback if still not valid
        if not refined_section.startswith('\\resume'):
            print(f"Warning: Failed to generate valid LaTeX during refinement. Using initial optimization.")
            return initial_optimization
        
        return refined_section