"""Agent for checking ATS compatibility of resumes with enhanced CAMEL integration."""

import re
import logging
from typing import Dict, Any, Tuple, List, Optional, Union

from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole
from camel.tasks import Task
from colorama import Fore, Style

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.text_utils import extract_score_from_text, extract_feedback_from_text

logger = logging.getLogger(__name__)

class ATSCompatibilityAgent(BaseOptimizerAgent):
    """Agent for checking ATS compatibility of resumes with enhanced CAMEL integration."""
    
    def __init__(self, model=None, verbose: bool = False):
        """Initialize the ATS compatibility agent.
        
        Args:
            model: Optional model to use
            verbose: Whether to print detailed output
        """
        super().__init__(
            role_name="ATS Compatibility Expert",
            system_message_content=(
                "You are an expert at evaluating resumes for ATS compatibility with over 10 years of experience in resume optimization. "
                "You provide detailed feedback on how to improve a resume to better pass ATS systems. "
                "You evaluate the resume against a specific job description and provide a score out of 100 "
                "along with detailed, specific feedback for improvements. "
                "You understand ATS algorithms and keyword matching techniques used by modern recruiting software. "
                "Your evaluation covers:\n"
                "1. Keyword match - How well the resume includes essential terms from the job description\n"
                "2. Format compatibility - How well the resume structure can be parsed by ATS systems\n"
                "3. Section organization - Whether the resume presents information in the optimal order\n"
                "4. Quantification - Whether achievements are properly quantified\n"
                "5. Terminology alignment - Whether the resume uses the same terminology as the job description"
            ),
            model=model,
            use_memory=True
        )
        self.verbose = verbose
    
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
    
    def check_compatibility(self, resume_content: str, job_description: str) -> Tuple[int, str, Dict[str, Any]]:
        """Check ATS compatibility of a resume against a job description.
        
        Args:
            resume_content: The full resume content
            job_description: The job description to check against
            
        Returns:
            Tuple of (score, feedback, detailed_metrics) where score is an integer 0-100,
            feedback is a string with improvement suggestions, and detailed_metrics is a dict
            with section-by-section analysis
        """
        # Save to memory for context retention
        self.save_to_memory(f"Job Description:\n{job_description}", role="user")
        self.save_to_memory(f"Resume Content:\n{resume_content}", role="user")
        
        if self.verbose:
            print(f"{Fore.CYAN}Checking ATS compatibility...{Style.RESET_ALL}")
        
        evaluation_message = (
            f"Evaluate this resume for ATS compatibility with the following job description:\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"RESUME:\n{resume_content}\n\n"
            f"Please provide a comprehensive evaluation with:\n"
            f"1. A score out of 100 for overall ATS compatibility\n"
            f"2. Section-by-section analysis with individual scores:\n"
            f"   - Professional Summary/Profile (score /100)\n"
            f"   - Technical Skills (score /100)\n"
            f"   - Work Experience (score /100)\n"
            f"   - Education (score /100)\n"
            f"3. Detailed feedback on how to improve the resume for better ATS performance, including:\n"
            f"   - Missing keywords that should be added\n"
            f"   - Sections that could be further optimized\n"
            f"   - Formatting suggestions for better ATS parsing\n"
            f"   - Overall assessment of how well the resume matches the job description\n\n"
            f"4. Top 5 keywords that are present in the job description but missing from the resume\n\n"
            f"Format your response with clear section headings and bullet points for actionable improvements."
        )
        
        # Get the response
        response = self.process(evaluation_message)
        
        # Save response to memory
        self.save_to_memory(response, role="assistant")
        
        # Extract score and feedback
        score = extract_score_from_text(response, default=75)
        feedback = extract_feedback_from_text(response)
        
        # Parse section-by-section analysis
        section_analysis = self._extract_section_analysis(response)
        
        # Extract missing keywords
        missing_keywords = self._extract_missing_keywords(response)
        
        # Compile detailed metrics
        detailed_metrics = {
            "overall_score": score,
            "section_scores": section_analysis,
            "missing_keywords": missing_keywords,
            "full_analysis": response
        }
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ ATS compatibility check complete{Style.RESET_ALL}")
            print(f"Overall Score: {score}/100")
            
            # Print section scores
            if section_analysis:
                print(f"{Fore.YELLOW}Section Scores:{Style.RESET_ALL}")
                for section, section_score in section_analysis.items():
                    print(f"  - {section}: {section_score}/100")
            
            # Print missing keywords
            if missing_keywords:
                print(f"{Fore.YELLOW}Missing Keywords:{Style.RESET_ALL}")
                for keyword in missing_keywords[:5]:
                    print(f"  - {keyword}")
        
        return score, feedback, detailed_metrics
    
    def process_task(self, task: Task) -> str:
        """Process a task to check ATS compatibility.
        
        Args:
            task: Task containing resume path and job description
            
        Returns:
            String representation of the ATS check results
        """
        from resume_optimizer.utils.latex_utils import read_latex_file
        
        # Extract required data from task
        if not hasattr(task, 'resume_path') or not task.resume_path:
            return "Error: Missing resume path in task"
            
        if not hasattr(task, 'job_description') or not task.job_description:
            return "Error: Missing job description in task"
        
        # Read the resume file
        resume_content = read_latex_file(str(task.resume_path))
        job_description = task.job_description
        
        # Perform ATS compatibility check
        score, feedback, detailed_metrics = self.check_compatibility(
            resume_content=resume_content,
            job_description=job_description
        )
        
        # Store result in task
        task.result = {
            "score": score,
            "feedback": feedback,
            "detailed_metrics": detailed_metrics
        }
        
        if self.verbose:
            print(f"{Fore.MAGENTA}ATS compatibility check complete for task: {task.id}{Style.RESET_ALL}")
        
        # Format response for task result
        result_text = (
            f"ATS Compatibility Score: {score}/100\n\n"
            f"Feedback:\n{feedback}"
        )
        
        return result_text
    
    def suggest_improvements(self, resume_content: str, job_description: str, ats_score: int, 
                          feedback: str) -> Dict[str, Any]:
        """Suggest specific improvements to increase ATS compatibility.
        
        Args:
            resume_content: The full resume content
            job_description: The job description to check against
            ats_score: Current ATS score
            feedback: Current feedback
            
        Returns:
            Dictionary with specific improvement suggestions
        """
        if self.verbose:
            print(f"{Fore.CYAN}Generating specific improvement suggestions...{Style.RESET_ALL}")
        
        improvement_prompt = (
            f"Based on this ATS compatibility evaluation:\n\n"
            f"SCORE: {ats_score}/100\n\n"
            f"FEEDBACK: {feedback}\n\n"
            f"Provide very specific, actionable improvements to increase the ATS compatibility score to 90+.\n\n"
            f"For each suggestion:\n"
            f"1. Specify the exact section to modify\n"
            f"2. Provide specific text or keywords to add\n"
            f"3. Indicate what text or content to replace or modify\n"
            f"4. Explain why this change will improve ATS performance\n\n"
            f"Focus on high-impact changes that will make the biggest difference in ATS performance."
        )
        
        response = self.process(improvement_prompt)
        
        # Save response to memory
        self.save_to_memory(response, role="assistant")
        
        # Parse suggestions into structured format
        suggestions = self._parse_improvement_suggestions(response)
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ Generated {len(suggestions)} improvement suggestions{Style.RESET_ALL}")
        
        return {
            "suggestions": suggestions,
            "raw_response": response
        }
    
    def _extract_section_analysis(self, response: str) -> Dict[str, int]:
        """Extract section-by-section analysis scores from the response.
        
        Args:
            response: The full analysis response
            
        Returns:
            Dictionary mapping section names to scores
        """
        section_scores = {}
        
        # Common section names to look for
        sections = ["Professional Summary", "Summary", "Profile", "Technical Skills", 
                   "Skills", "Work Experience", "Experience", "Education"]
        
        for section in sections:
            # Look for patterns like "Section Name: 85/100" or "Section Name (85/100)"
            pattern = fr"{section}:?\s*(?:score:?\s*)?(\d+)(?:\s*/\s*|\s+out\s+of\s+)100"
            match = re.search(pattern, response, re.IGNORECASE)
            
            if match:
                score = int(match.group(1))
                section_scores[section] = score
        
        return section_scores
    
    def _extract_missing_keywords(self, response: str) -> List[str]:
        """Extract missing keywords from the response.
        
        Args:
            response: The full analysis response
            
        Returns:
            List of missing keywords
        """
        missing_keywords = []
        
        # Look for sections with missing keywords
        patterns = [
            r"Missing [Kk]eywords:(.*?)(?:\n\n|\n[A-Z])",
            r"missing keywords?(?:\s+include)?(?:\s*:|(?:\s+are)?)(.*?)(?:\n\n|\n[A-Z])",
            r"Top \d+ [Mm]issing [Kk]eywords:(.*?)(?:\n\n|\n[A-Z])"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                keyword_text = match.group(1).strip()
                
                # Extract keywords from bullet points or commas
                if "-" in keyword_text or "•" in keyword_text:
                    # Extract from bullet points
                    bullet_keywords = re.findall(r"[-•]\s*(.*?)(?:\n|$)", keyword_text)
                    missing_keywords.extend([k.strip() for k in bullet_keywords if k.strip()])
                else:
                    # Extract from comma-separated list
                    comma_keywords = [k.strip() for k in keyword_text.split(",") if k.strip()]
                    missing_keywords.extend(comma_keywords)
                
                # If we found keywords, break the loop
                if missing_keywords:
                    break
        
        return missing_keywords
    
    def _parse_improvement_suggestions(self, response: str) -> List[Dict[str, str]]:
        """Parse improvement suggestions into a structured format.
        
        Args:
            response: The suggestions response
            
        Returns:
            List of dictionaries containing structured suggestions
        """
        suggestions = []
        
        # Extract suggestions that are often formatted as numbered or bulleted lists
        suggestion_patterns = [
            # Match numbered suggestions
            r"(\d+)\.\s+(.*?)(?=\n\d+\.|\n\n|$)",
            # Match bulleted suggestions
            r"[-•]\s+(.*?)(?=\n[-•]|\n\n|$)"
        ]
        
        found_suggestions = []
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # For numbered lists, the content is in group 2
                        content = match[1].strip()
                    else:
                        # For bullet lists, the content is the whole match
                        content = match.strip()
                    
                    found_suggestions.append(content)
        
        # Process each suggestion to extract structured information
        for suggestion_text in found_suggestions:
            # Try to identify the section being referenced
            section_match = re.search(r"(?:in|for|update|modify|revise|improve)\s+the\s+([A-Za-z\s]+)\s+section", suggestion_text, re.IGNORECASE)
            section = section_match.group(1).strip() if section_match else "General"
            
            # Try to extract what to add
            add_match = re.search(r"add\s+(?:the\s+)?(?:keyword|term|phrase|skill|bullet)s?:?\s+(.*?)(?:\.|$|\n)", suggestion_text, re.IGNORECASE)
            to_add = add_match.group(1).strip() if add_match else ""
            
            # Try to extract what to remove or replace
            remove_match = re.search(r"(?:remove|replace)\s+(?:the\s+)?(?:keyword|term|phrase|skill|bullet)s?:?\s+(.*?)(?:\.|$|\n)", suggestion_text, re.IGNORECASE)
            to_remove = remove_match.group(1).strip() if remove_match else ""
            
            # The rest is the explanation
            explanation = suggestion_text
            
            suggestions.append({
                "section": section,
                "suggestion": suggestion_text,
                "to_add": to_add,
                "to_remove": to_remove,
                "explanation": explanation
            })
        
        return suggestions