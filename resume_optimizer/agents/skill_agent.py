"""Agent for optimizing the technical skills section of a resume with enhanced CAMEL integration."""

import logging
from typing import Dict, Any, Optional, List, Union

from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole
from camel.tasks import Task
from colorama import Fore, Style

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.latex_utils import extract_latex_content
from resume_optimizer.utils.text_utils import format_analysis_for_prompt

logger = logging.getLogger(__name__)

class SkillOptimizerAgent(BaseOptimizerAgent):
    """Agent for optimizing the technical skills section of a resume with enhanced CAMEL integration."""
    
    def __init__(self, model=None, verbose: bool = False):
        """Initialize the skill optimizer agent.
        
        Args:
            model: Optional model to use
            verbose: Whether to print detailed output
        """
        super().__init__(
            role_name="Technical Skills Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing technical skills sections to perfectly match job descriptions. "
                "You understand how to add and remove skills strategically while maintaining the original LaTeX formatting. "
                "You follow these key principles:\n"
                "1. Match terminology exactly to what's used in the job description\n"
                "2. Organize skills into logical categories that highlight transferable abilities\n"
                "3. Prioritize required and preferred skills from the job analysis\n"
                "4. Remove irrelevant skills that might distract from core qualifications\n"
                "5. Add high-value skills mentioned in the job description but missing from the resume"
            ),
            model=model,
            use_memory=True
        )
        self.verbose = verbose
        self.optimization_attempts = 0
        self.max_attempts = 3
    
    def optimize(self, skills_section: str, jd_analysis: Dict[str, Any]) -> str:
        """Optimize the technical skills section based on job description analysis.
        
        Args:
            skills_section: The original technical skills section content
            jd_analysis: The job description analysis results
            
        Returns:
            Optimized technical skills section content
        """
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(jd_analysis)
        
        # Save to memory for context retention
        self.save_to_memory(f"Job Analysis:\n{job_analysis_text}", role="user")
        self.save_to_memory(f"Original Skills Section:\n{skills_section}", role="user")
        
        if self.verbose:
            print(f"{Fore.CYAN}Optimizing technical skills section...{Style.RESET_ALL}")
        
        # Create the specialized prompt for skills optimization
        skills_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Technical Skill Section: \n\n<Resume Technical Skill Section Start>\n{skills_section}\n<Resume Technical Skill Section End>\n\n"
            f"Your job is to optimize this technical skills section to achieve the highest possible ATS match score (90%+) by:\n\n"
            f"1. Add ALL keywords or skills or tech from the job description that are missing from the existing skill section\n"
            f"2. Place each skill into an appropriate subcategory (like Programming Languages, Cloud Platforms, etc.)\n"
            f"3. If you need to create a new subcategory to organize skills better, do so\n"
            f"4. Remove skills which are not relevant to the job description or have low scores in the analysis\n"
            f"5. Prioritize skills listed as REQUIRED in the analysis (ensure they appear first in their categories)\n"
            f"6. Ensure you maintain the EXACT LaTeX formatting as in the original\n\n"
            f"IMPORTANT: Give me the updated skill section in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current skills section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(skills_prompt)
        optimized_skills = extract_latex_content(response)
        
        # Save optimized version to memory
        self.save_to_memory(f"Optimized Skills Section:\n{optimized_skills}", role="assistant")
        
        # If we couldn't extract valid content, try one more time with clearer instructions
        if not optimized_skills.startswith('\\resume'):
            self.optimization_attempts += 1
            if self.verbose:
                print(f"{Fore.YELLOW}Refining skills section format (attempt {self.optimization_attempts})...{Style.RESET_ALL}")
                
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
            logger.warning("Failed to generate valid LaTeX for skills section. Using original content.")
            if self.verbose:
                print(f"{Fore.RED}Could not generate valid LaTeX. Using original content.{Style.RESET_ALL}")
            return skills_section
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ Skills section optimized successfully{Style.RESET_ALL}")
        
        return optimized_skills
    
    def refine_with_feedback(self, initial_optimization: str, feedback: str, jd_analysis: Dict[str, Any]) -> str:
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
        
        # Save feedback to memory
        self.save_to_memory(f"Optimization Feedback:\n{feedback}", role="user")
        
        if self.verbose:
            print(f"{Fore.CYAN}Refining skills section based on feedback...{Style.RESET_ALL}")
        
        feedback_prompt = (
            f"Refine this skills section based on the evaluation feedback:\n\n"
            f"JOB ANALYSIS:\n{job_analysis_text}\n\n"
            f"CURRENT SECTION:\n{initial_optimization}\n\n"
            f"FEEDBACK:\n{feedback}\n\n"
            f"Please incorporate ALL the feedback to improve this section. "
            f"Make sure to address all missed opportunities and suggestions while maintaining "
            f"the proper LaTeX format. Return ONLY the improved LaTeX code."
        )
        
        response = self.process(feedback_prompt)
        refined_section = extract_latex_content(response)
        
        # Save refined version to memory
        self.save_to_memory(f"Refined Skills Section:\n{refined_section}", role="assistant")
        
        # If extraction failed, try clarification
        if not refined_section.startswith('\\resume'):
            self.optimization_attempts += 1
            if self.verbose:
                print(f"{Fore.YELLOW}Refining skills section format (attempt {self.optimization_attempts})...{Style.RESET_ALL}")
                
            clarification_message = (
                "Your response wasn't formatted correctly. I need ONLY raw LaTeX code "
                "starting with \\resumeSubHeadingListStart and ending with \\resumeSubHeadingListEnd. "
                "No explanation, no markdown formatting, just the raw LaTeX code like in the original. "
                "Please try again with ONLY the LaTeX code."
            )
            response = self.process(clarification_message)
            refined_section = extract_latex_content(response)
        
        # Final fallback if still not valid
        if not refined_section.startswith('\\resume'):
            logger.warning("Failed to generate valid LaTeX during refinement. Using initial optimization.")
            if self.verbose:
                print(f"{Fore.RED}Could not generate valid refinement. Using initial optimization.{Style.RESET_ALL}")
            return initial_optimization
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ Skills section refined successfully{Style.RESET_ALL}")
        
        return refined_section
        
    def process_task(self, task: Task) -> str:
        """Process a task to optimize a skills section.
        
        Args:
            task: Task containing section content and analysis results
            
        Returns:
            Optimized section content
        """
        # Extract required data from task
        if not hasattr(task, 'section_name') or not task.section_name:
            return "Error: Missing section name in task"
            
        if not hasattr(task, 'section_content') or not task.section_content:
            return "Error: Missing section content in task"
            
        if not hasattr(task, 'analysis_results') or not task.analysis_results:
            return "Error: Missing analysis results in task"
            
        section_name = task.section_name
        section_content = task.section_content
        analysis_results = task.analysis_results
        
        # Perform optimization
        optimized_content = self.optimize(section_content, analysis_results)
        
        # Store result in task
        task.result = {
            "optimized_content": optimized_content,
            "section_name": section_name
        }
        
        if self.verbose:
            print(f"{Fore.MAGENTA}Skills section optimization complete for task: {task.id}{Style.RESET_ALL}")
        
        return optimized_content
    
    def compare_skills(self, original_section: str, optimized_section: str, jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare original and optimized skills to extract metrics.
        
        Args:
            original_section: Original skills section
            optimized_section: Optimized skills section
            jd_analysis: Job description analysis
            
        Returns:
            Dictionary with comparison metrics
        """
        # Get required skills from analysis
        required_skills = []
        for skill in jd_analysis.get("technical_skills", []):
            if skill.get("score", 0) >= 7 or skill.get("skill") in jd_analysis.get("required", []):
                required_skills.append(skill.get("skill", "").lower())
        
        # Extract skills from sections (simple implementation)
        original_skills = self._extract_skills_from_latex(original_section)
        optimized_skills = self._extract_skills_from_latex(optimized_section)
        
        # Calculate metrics
        added_skills = [s for s in optimized_skills if s.lower() not in [os.lower() for os in original_skills]]
        removed_skills = [s for s in original_skills if s.lower() not in [os.lower() for os in optimized_skills]]
        
        # Calculate relevance scores
        original_relevant = sum(1 for s in original_skills if any(rs in s.lower() for rs in required_skills))
        optimized_relevant = sum(1 for s in optimized_skills if any(rs in s.lower() for rs in required_skills))
        
        # Improvement percentage
        if len(required_skills) > 0:
            original_match = (original_relevant / len(required_skills)) * 100
            optimized_match = (optimized_relevant / len(required_skills)) * 100
            improvement = optimized_match - original_match
        else:
            original_match = 0
            optimized_match = 0
            improvement = 0
        
        return {
            "original_skill_count": len(original_skills),
            "optimized_skill_count": len(optimized_skills),
            "added_skills": added_skills,
            "removed_skills": removed_skills,
            "required_skill_count": len(required_skills),
            "original_match_percentage": original_match,
            "optimized_match_percentage": optimized_match,
            "improvement_percentage": improvement
        }
    
    def _extract_skills_from_latex(self, latex_content: str) -> List[str]:
        """Extract skills from LaTeX content.
        
        Args:
            latex_content: LaTeX content to extract skills from
            
        Returns:
            List of extracted skills
        """
        skills = []
        lines = latex_content.split('\n')
        
        for line in lines:
            # Look for text after & in tabularx rows
            if '&' in line:
                skill_text = line.split('&')[1].strip()
                # Remove LaTeX commands and split by commas
                skill_text = skill_text.replace('\\\\', '')
                skills.extend([s.strip() for s in skill_text.split(',')])
        
        return [s for s in skills if s]  # Remove empty strings