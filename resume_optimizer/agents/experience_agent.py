"""Agent for optimizing the work experience section of a resume with enhanced CAMEL integration."""

import logging
import re
from typing import Dict, Any, Optional, List, Union

from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole
from camel.tasks import Task
from colorama import Fore, Style

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.latex_utils import extract_latex_content
from resume_optimizer.utils.text_utils import format_analysis_for_prompt

logger = logging.getLogger(__name__)

class ExperienceOptimizerAgent(BaseOptimizerAgent):
    """Agent for optimizing the work experience section of a resume with enhanced CAMEL integration."""
    
    def __init__(self, model=None, verbose: bool = False):
        """Initialize the experience optimizer agent.
        
        Args:
            model: Optional model to use
            verbose: Whether to print detailed output
        """
        super().__init__(
            role_name="Work Experience Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing work experience sections to perfectly match job descriptions. "
                "You know how to incorporate keywords, hard skills, soft skills, and action words while maintaining "
                "the original format and integrity of accomplishments by 30 percent. "
                "You follow these key principles:\n"
                "1. Use strong, unique action verbs at the beginning of each bullet point\n"
                "2. Include specific metrics and quantifiable achievements\n"
                "3. Incorporate keywords and terminology from the job description\n"
                "4. Highlight leadership, technical expertise, and business impact\n"
                "5. Remove or modify irrelevant experience points\n"
                "You feel free to add or remove bullet points based on alignment with the job description."
            ),
            model=model,
            use_memory=True
        )
        self.verbose = verbose
        self.optimization_attempts = 0
        self.max_attempts = 3
        
        # List of strong action verbs for resume bullets
        self.action_words = [
            "Spearheaded", "Orchestrated", "Catalyzed", "Implemented", "Pioneered", 
            "Transformed", "Streamlined", "Revolutionized", "Overhauled", "Innovated", 
            "Leveraged", "Optimized", "Negotiated", "Cultivated", "Accelerated", 
            "Championed", "Executed", "Launched", "Redesigned", "Maximized", 
            "Engineered", "Strategized", "Revitalized", "Conceptualized", "Facilitated", 
            "Generated", "Amplified", "Consolidated", "Instituted", "Reengineered", 
            "Mobilized", "Formulated", "Mentored", "Synthesized", "Drove", 
            "Propelled", "Reconciled", "Galvanized", "Expedited"
        ]
    
    def optimize(self, experience_section: str, jd_analysis: Dict[str, Any]) -> str:
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
        
        # Save to memory for context retention
        self.save_to_memory(f"Job Analysis:\n{job_analysis_text}", role="user")
        self.save_to_memory(f"Original Experience Section:\n{experience_section}", role="user")
        
        if self.verbose:
            print(f"{Fore.CYAN}Optimizing work experience section...{Style.RESET_ALL}")
        
        # Create the specialized prompt for experience optimization
        experience_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Work Experience Section: \n\n<Resume Work Experience Section Start>\n{experience_section}\n<Resume Work Experience Section End>\n\n"
            f"I would like you to make the work experience section extremely well-tailored to incorporate ALL the keywords, hard skills, and soft skills from the job analysis."
            f"Your goal is to make the Work Experience section completely customized for the job by:\n\n"
            f"1. Using ALL keywords and required skills from the job analysis in the bullet points\n"
            f"2. Starting each bullet with one of these strong action verbs: {action_words_text}\n"
            f"3. Making each bullet point 16-18 words long with clear metrics and achievements\n"
            f"4. Ensuring each bullet highlights achievements relevant to the job requirements\n"
            f"5. Using the EXACT terminology from the job description for maximum ATS compatibility\n"
            f"6. Emphasizing leadership, technical expertise, and business impact that matches the job's requirements\n\n"
            f"IMPORTANT: Give me the updated experience section in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current experience section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(experience_prompt)
        optimized_experience = extract_latex_content(response)
        
        # Save optimized version to memory
        self.save_to_memory(f"Optimized Experience Section:\n{optimized_experience}", role="assistant")
        
        # If we couldn't extract valid content, try one more time with clearer instructions
        if not optimized_experience.startswith('\\resume'):
            self.optimization_attempts += 1
            if self.verbose:
                print(f"{Fore.YELLOW}Refining experience section format (attempt {self.optimization_attempts})...{Style.RESET_ALL}")
                
            clarification_message = (
                "Your response wasn't formatted correctly. I need ONLY raw LaTeX code "
                "starting with \\resumeSubHeadingListStart and ending with \\resumeSubHeadingListEnd. "
                "No explanation, no markdown formatting, just the raw LaTeX code like in the original. "
                "Please try again with ONLY the LaTeX code."
            )
            response = self.process(clarification_message)
            optimized_experience = extract_latex_content(response)
            
        # Final validation to ensure we have valid LaTeX
        if not optimized_experience.startswith('\\resume'):
            logger.warning("Failed to generate valid LaTeX for experience section. Using original content.")
            if self.verbose:
                print(f"{Fore.RED}Could not generate valid LaTeX. Using original content.{Style.RESET_ALL}")
            return experience_section
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ Experience section optimized successfully{Style.RESET_ALL}")
        
        return optimized_experience
    
    def refine_with_feedback(self, initial_optimization: str, feedback: str, jd_analysis: Dict[str, Any]) -> str:
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
        
        # Save feedback to memory
        self.save_to_memory(f"Optimization Feedback:\n{feedback}", role="user")
        
        if self.verbose:
            print(f"{Fore.CYAN}Refining experience section based on feedback...{Style.RESET_ALL}")
        
        feedback_prompt = (
            f"Refine this experience section based on the evaluation feedback:\n\n"
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
        self.save_to_memory(f"Refined Experience Section:\n{refined_section}", role="assistant")
        
        # If extraction failed, try clarification
        if not refined_section.startswith('\\resume'):
            self.optimization_attempts += 1
            if self.verbose:
                print(f"{Fore.YELLOW}Refining experience section format (attempt {self.optimization_attempts})...{Style.RESET_ALL}")
                
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
            print(f"{Fore.GREEN}✅ Experience section refined successfully{Style.RESET_ALL}")
        
        return refined_section
    
    def process_task(self, task: Task) -> str:
        """Process a task to optimize an experience section.
        
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
            print(f"{Fore.MAGENTA}Experience section optimization complete for task: {task.id}{Style.RESET_ALL}")
        
        return optimized_content
    
    def analyze_action_verbs(self, section_content: str) -> Dict[str, Any]:
        """Analyze the action verbs used in the experience section.
        
        Args:
            section_content: The experience section content
            
        Returns:
            Dictionary with action verb analysis
        """
        lines = section_content.split('\n')
        bullets = []
        
        # Extract bullet points
        for line in lines:
            if '\\resumeItem{' in line:
                # Extract content between curly braces
                match = re.search(r'\\resumeItem{(.*?)}', line)
                if match:
                    bullet = match.group(1)
                    bullets.append(bullet)
        
        # Analyze action verbs
        action_verbs = []
        for bullet in bullets:
            # Get the first word of each bullet
            words = bullet.split()
            if words:
                first_word = words[0].strip().rstrip('.,:;')
                action_verbs.append(first_word)
        
        # Count unique verbs
        unique_verbs = len(set(action_verbs))
        strong_verbs = len([v for v in action_verbs if v in self.action_words])
        
        return {
            "total_bullets": len(bullets),
            "action_verbs": action_verbs,
            "unique_verbs": unique_verbs,
            "strong_verbs": strong_verbs,
            "strong_verb_percentage": (strong_verbs / len(bullets) * 100) if bullets else 0
        }
    
    def extract_metrics(self, section_content: str) -> List[str]:
        """Extract metrics and quantified achievements from the experience section.
        
        Args:
            section_content: The experience section content
            
        Returns:
            List of extracted metrics
        """
        # Regular expressions to find metrics (numbers with % or other units)
        metric_patterns = [
            r'(\d+(?:\.\d+)?%)',  # Percentages
            r'(\$\d+(?:,\d+)*(?:\.\d+)?(?:\s*[KkMmBbTt])?)',  # Dollar amounts
            r'(\d+(?:,\d+)*(?:\s*[KkMmBbTt])?\+?(?:\s*users|developers|customers|clients)?)',  # Numbers with K/M/B/T
            r'(\d+(?:,\d+)*\s*hours?)',  # Hours
            r'(\d+(?:,\d+)*\s*days?)',  # Days
            r'(\d+(?:,\d+)*\s*weeks?)',  # Weeks
            r'(\d+(?:,\d+)*\s*months?)',  # Months
            r'(\d+(?:,\d+)*\s*years?)',  # Years
            r'(increased|decreased|reduced|improved|enhanced|boosted|accelerated)\s+by\s+(\d+(?:\.\d+)?%)',  # Improvements
            r'(from|to)\s+(\d+(?:\.\d+)?%)'  # From/to metrics
        ]
        
        metrics = []
        lines = section_content.split('\n')
        
        for line in lines:
            for pattern in metric_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            metrics.append(' '.join(match))
                        else:
                            metrics.append(match)
        
        return metrics