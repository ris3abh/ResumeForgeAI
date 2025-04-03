"""Agent for optimizing the technical skills section of a resume."""

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.latex_utils import extract_latex_content
from resume_optimizer.utils.text_utils import format_analysis_for_prompt


class SkillOptimizerAgent(BaseOptimizerAgent):
    """Agent for optimizing the technical skills section of a resume."""
    
    def __init__(self, model=None):
        """Initialize the skill optimizer agent.
        
        Args:
            model: Optional model to use
        """
        super().__init__(
            role_name="Technical Skills Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing technical skills sections to perfectly match job descriptions. "
                "You understand how to add and remove skills strategically while maintaining the original LaTeX formatting."
            ),
            model=model
        )
    
    def optimize(self, skills_section, jd_analysis):
        """Optimize the technical skills section based on job description analysis.
        
        Args:
            skills_section: The original technical skills section content
            jd_analysis: The job description analysis results
            
        Returns:
            Optimized technical skills section content
        """
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(jd_analysis)
        
        # Create the specialized prompt for skills optimization
        skills_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Technical Skill Section: \n\n<Resume Technical Skill Section Start>\n{skills_section}\n<Resume Technical Skill Section End>\n\n"
            f"Your job is to:\n"
            f"1. Add keywords or skills or tech that you feel are missing from the existing skill section.\n"
            f"2. Place them into a specific subcategory like mentioned in the skill section. If you cannot find a subcategory to place it in, create one.\n"
            f"3. Remove keywords or skills or tech which you feel are not relevant to the job description or have low scores in the analysis.\n"
            f"4. Prioritize skills listed as critical requirements or required skills in the analysis.\n\n"
            f"IMPORTANT: Give the updated skill section in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or AI assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current skills section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(skills_prompt)
        optimized_skills = extract_latex_content(response)
        
        # If we couldn't extract valid content, try one more time with clearer instructions
        if not optimized_skills.startswith('\\resume'):
            clarification_message = (
                "Your response wasn't formatted correctly. I need ONLY raw LaTeX code "
                "starting with \\resumeSubHeadingListStart and ending with \\resumeSubHeadingListEnd. "
                "No explanation, no markdown formatting, just the raw LaTeX code like in the original. "
                "Please try again with ONLY the LaTeX code."
            )
            response = self.process(clarification_message)
            optimized_skills = extract_latex_content(response)
            
        # Final validation to ensure we have valid LaTeX
        if not optimized_skills.startswith('\\resume'):
            print(f"Warning: Failed to generate valid LaTeX for skills section. Using original content.")
            return skills_section
        
        return optimized_skills
    
    def refine_with_feedback(self, initial_optimization, feedback, jd_analysis):
        """Refine the optimized skills section based on feedback.
        
        Args:
            initial_optimization: The initial optimized skills section
            feedback: Feedback on the initial optimization
            jd_analysis: The job description analysis
            
        Returns:
            Refined skills section content
        """
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(jd_analysis)
        
        feedback_prompt = (
            f"Refine this skills section based on the evaluation feedback:\n\n"
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