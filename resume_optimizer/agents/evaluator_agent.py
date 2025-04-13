"""Agent for evaluating resume section optimizations with enhanced CAMEL integration."""

import re
import logging
from typing import Dict, Any, Tuple, List, Optional, Union

from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole
from camel.tasks import Task
from colorama import Fore, Style

from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.text_utils import format_analysis_for_prompt

logger = logging.getLogger(__name__)

class EvaluatorAgent(BaseOptimizerAgent):
    """Agent for evaluating optimized resume sections with enhanced CAMEL integration."""
    
    def __init__(self, model=None, verbose: bool = False):
        """Initialize the evaluator agent.
        
        Args:
            model: Optional model to use
            verbose: Whether to print detailed output
        """
        super().__init__(
            role_name="Resume Optimization Evaluator",
            system_message_content=(
                "You are an expert at evaluating resume optimizations. You can compare "
                "an optimized resume section against the original and the job description analysis "
                "to identify missed opportunities and areas for improvement. Your feedback is specific, "
                "actionable, and focused on maximizing ATS compatibility and human appeal. "
                "You evaluate based on these criteria:\n"
                "1. Keyword inclusion - Whether all key terms from the job description are included\n"
                "2. Relevance - How well the content aligns with job requirements\n"
                "3. Formatting - Whether the format is ATS-friendly and visually appealing\n"
                "4. Impact - Whether achievements are quantified and impactful\n"
                "5. Improvement - How much better the optimized version is compared to the original"
            ),
            model=model,
            use_memory=True
        )
        self.verbose = verbose
    
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
    
    def evaluate_section(self, section_type: str, original_section: str, optimized_section: str, 
                       analysis_results: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Evaluate optimization and provide feedback for improvement.
        
        Args:
            section_type: Type of section ("skills" or "experience")
            original_section: Original section content
            optimized_section: Optimized section content
            analysis_results: Job description analysis results
            
        Returns:
            Tuple of (evaluation feedback, metrics dictionary)
        """
        # Create specific criteria based on section type
        if section_type.lower() == "skills" or section_type.lower() == "technical skills":
            criteria = (
                "1. Inclusion of all hard skills from the analysis\n"
                "2. Appropriate organization of skills into categories\n"
                "3. Prioritization of required skills\n"
                "4. Removal of irrelevant skills\n"
                "5. Proper terminology matching with the job description"
            )
        elif section_type.lower() == "experience" or section_type.lower() == "work experience":
            criteria = (
                "1. Use of all keywords from job description in the work experience bullet points\n"
                "2. Incorporation of both hard and soft skills\n"
                "3. Use of strong action verbs\n"
                "4. Quantifiable achievements and metrics\n"
                "5. Relevance of highlighted experiences to job requirements"
            )
        elif section_type.lower() == "summary" or section_type.lower() == "professional summary":
            criteria = (
                "1. Concise overview of key qualifications aligned with the job\n"
                "2. Inclusion of top 3-5 required skills\n"
                "3. Emphasis on experience level that matches job requirements\n"
                "4. Proper length (2-4 lines)\n"
                "5. Compelling value proposition for the specific role"
            )
        else:
            criteria = (
                "1. Alignment with job requirements\n"
                "2. Inclusion of relevant keywords\n"
                "3. Proper formatting for ATS\n"
                "4. Emphasis on relevant information\n"
                "5. Improvement over original content"
            )
        
        # Save to memory for context retention
        self.save_to_memory(f"Section Type: {section_type}", role="user")
        self.save_to_memory(f"Original Section:\n{original_section}", role="user")
        self.save_to_memory(f"Optimized Section:\n{optimized_section}", role="user")
        
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(analysis_results)
        
        if self.verbose:
            print(f"{Fore.CYAN}Evaluating {section_type} section optimization...{Style.RESET_ALL}")
        
        evaluation_prompt = (
            f"Evaluate this optimized {section_type} section against the job description analysis:\n\n"
            f"JOB ANALYSIS:\n{job_analysis_text}\n\n"
            f"ORIGINAL SECTION:\n{original_section}\n\n"
            f"OPTIMIZED SECTION:\n{optimized_section}\n\n"
            f"Evaluate against these criteria:\n{criteria}\n\n"
            f"Please provide a comprehensive evaluation with:\n"
            f"1. An overall assessment score (1-10)\n"
            f"2. Scores for each of the 5 criteria (1-10)\n"
            f"3. Specific missed opportunities\n"
            f"4. Detailed suggestions for improvement\n"
            f"5. Any keywords or skills that should be added\n"
            f"6. Any content that should be rephrased or removed\n\n"
            f"Format your response with clear section headings for easy reference."
        )
        
        response = self.process(evaluation_prompt)
        
        # Save response to memory
        self.save_to_memory(response, role="assistant")
        
        # Extract metrics from the evaluation
        metrics = self._extract_evaluation_metrics(response, section_type)
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ {section_type} section evaluation complete{Style.RESET_ALL}")
            print(f"Overall Score: {metrics.get('overall_score', 'N/A')}/10")
            
            # Print criteria scores
            if metrics.get('criteria_scores'):
                print(f"{Fore.YELLOW}Criteria Scores:{Style.RESET_ALL}")
                for criterion, score in metrics.get('criteria_scores', {}).items():
                    print(f"  - {criterion}: {score}/10")
        
        return response, metrics
    
    def process_task(self, task: Task) -> str:
        """Process a task to evaluate an optimized section.
        
        Args:
            task: Task containing original content, optimized content, and analysis results
            
        Returns:
            Evaluation feedback as string
        """
        # Extract required data from task
        if not hasattr(task, 'section_name') or not task.section_name:
            return "Error: Missing section name in task"
            
        if not hasattr(task, 'section_content') or not task.section_content:
            return "Error: Missing original section content in task"
            
        if not hasattr(task, 'optimized_content') or not task.optimized_content:
            return "Error: Missing optimized content in task"
            
        if not hasattr(task, 'analysis_results') or not task.analysis_results:
            return "Error: Missing analysis results in task"
            
        section_name = task.section_name
        original_content = task.section_content
        optimized_content = task.optimized_content
        analysis_results = task.analysis_results
        
        # Perform evaluation
        evaluation, metrics = self.evaluate_section(
            section_type=section_name,
            original_section=original_content,
            optimized_section=optimized_content,
            analysis_results=analysis_results
        )
        
        # Store result in task
        task.result = {
            "evaluation": evaluation,
            "metrics": metrics
        }
        
        if self.verbose:
            print(f"{Fore.MAGENTA}Section evaluation complete for task: {task.id}{Style.RESET_ALL}")
        
        return evaluation
    
    def _extract_evaluation_metrics(self, evaluation: str, section_type: str) -> Dict[str, Any]:
        """Extract metrics from the evaluation text.
        
        Args:
            evaluation: The evaluation text
            section_type: Type of section being evaluated
            
        Returns:
            Dictionary with extracted metrics
        """
        metrics = {
            "section_type": section_type,
            "overall_score": None,
            "criteria_scores": {},
            "missed_opportunities": [],
            "improvement_suggestions": [],
            "keywords_to_add": [],
            "content_to_remove": []
        }
        
        # Extract overall score
        overall_match = re.search(r'(?:overall|assessment)[^0-9]*?(\d+)(?:/| out of |/| of )10', evaluation, re.IGNORECASE)
        if overall_match:
            metrics["overall_score"] = int(overall_match.group(1))
        
        # Extract criteria scores
        criteria_patterns = [
            r'(?:Criterion|Criteria) (\d+)[^0-9]*?(\d+)(?:/| out of |/| of )10',
            r'(\d+)\.\s+[^:]+:\s*(\d+)(?:/| out of |/| of )10',
            r'([A-Za-z\s]+):\s*(\d+)(?:/| out of |/| of )10'
        ]
        
        for pattern in criteria_patterns:
            criteria_matches = re.findall(pattern, evaluation, re.IGNORECASE)
            if criteria_matches:
                for criterion, score in criteria_matches:
                    metrics["criteria_scores"][criterion.strip()] = int(score)
                break  # Use first matching pattern
        
        # Extract missed opportunities
        opportunities_match = re.search(r'(?:Missed Opportunities|Opportunities)[:\s]+(.*?)(?:(?:Detailed )?Suggestions|Improvements|Keywords|$)', evaluation, re.DOTALL | re.IGNORECASE)
        if opportunities_match:
            opportunities_text = opportunities_match.group(1).strip()
            # Extract bullet points
            if '-' in opportunities_text:
                opportunities = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', opportunities_text, re.DOTALL)
                metrics["missed_opportunities"] = [opp.strip() for opp in opportunities if opp.strip()]
            else:
                # Just use paragraphs
                opportunities = [p.strip() for p in opportunities_text.split('\n') if p.strip()]
                metrics["missed_opportunities"] = opportunities
        
        # Extract improvement suggestions
        suggestions_match = re.search(r'(?:Suggestions|Improvements)[:\s]+(.*?)(?:Keywords|Content|$)', evaluation, re.DOTALL | re.IGNORECASE)
        if suggestions_match:
            suggestions_text = suggestions_match.group(1).strip()
            # Extract bullet points
            if '-' in suggestions_text:
                suggestions = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', suggestions_text, re.DOTALL)
                metrics["improvement_suggestions"] = [sugg.strip() for sugg in suggestions if sugg.strip()]
            else:
                # Just use paragraphs
                suggestions = [p.strip() for p in suggestions_text.split('\n') if p.strip()]
                metrics["improvement_suggestions"] = suggestions
        
        # Extract keywords to add
        keywords_match = re.search(r'(?:Keywords|Skills)[^:]*?[aA]dd[^:]*?:(.*?)(?:Content|Remove|$)', evaluation, re.DOTALL | re.IGNORECASE)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            # Try to extract as comma-separated list or bullet points
            if ',' in keywords_text:
                keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
                metrics["keywords_to_add"] = keywords
            elif '-' in keywords_text:
                keywords = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', keywords_text, re.DOTALL)
                metrics["keywords_to_add"] = [k.strip() for k in keywords if k.strip()]
            else:
                # Just use entire text
                metrics["keywords_to_add"] = [keywords_text]
        
        # Extract content to remove
        remove_match = re.search(r'(?:Content|Remove|Rephrase)[^:]*?:(.*?)(?:\n\n|$)', evaluation, re.DOTALL | re.IGNORECASE)
        if remove_match:
            remove_text = remove_match.group(1).strip()
            # Try to extract as bullet points
            if '-' in remove_text:
                remove_items = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', remove_text, re.DOTALL)
                metrics["content_to_remove"] = [item.strip() for item in remove_items if item.strip()]
            else:
                # Just use paragraphs
                remove_items = [p.strip() for p in remove_text.split('\n') if p.strip()]
                metrics["content_to_remove"] = remove_items
        
        return metrics
    
    def compare_versions(self, original_section: str, optimized_section: str) -> Dict[str, Any]:
        """Compare the original and optimized sections for key differences.
        
        Args:
            original_section: Original section content
            optimized_section: Optimized section content
            
        Returns:
            Dictionary with comparison metrics
        """
        if self.verbose:
            print(f"{Fore.CYAN}Comparing original and optimized sections...{Style.RESET_ALL}")
        
        comparison_prompt = (
            f"Compare the original and optimized resume sections below. "
            f"Identify key differences, improvements, and any potential issues.\n\n"
            f"ORIGINAL SECTION:\n{original_section}\n\n"
            f"OPTIMIZED SECTION:\n{optimized_section}\n\n"
            f"Please provide:\n"
            f"1. A list of key content that was added\n"
            f"2. A list of content that was removed\n"
            f"3. A list of content that was rephrased\n"
            f"4. An overall assessment of whether the changes improved the section\n"
            f"For each identified change, include the exact text involved."
        )
        
        response = self.process(comparison_prompt)
        
        # Extract key metrics from the comparison
        added_content = []
        removed_content = []
        rephrased_content = []
        improvement_assessment = ""
        
        # Extract added content
        added_match = re.search(r'(?:Added|Additions)[^:]*?:(.*?)(?:Removed|Removal|Rephrased|Overall|$)', response, re.DOTALL | re.IGNORECASE)
        if added_match:
            added_text = added_match.group(1).strip()
            if '-' in added_text:
                added_items = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', added_text, re.DOTALL)
                added_content = [item.strip() for item in added_items if item.strip()]
            else:
                added_content = [added_text]
        
        # Extract removed content
        removed_match = re.search(r'(?:Removed|Removal)[^:]*?:(.*?)(?:Rephrased|Added|Overall|$)', response, re.DOTALL | re.IGNORECASE)
        if removed_match:
            removed_text = removed_match.group(1).strip()
            if '-' in removed_text:
                removed_items = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', removed_text, re.DOTALL)
                removed_content = [item.strip() for item in removed_items if item.strip()]
            else:
                removed_content = [removed_text]
        
        # Extract rephrased content
        rephrased_match = re.search(r'(?:Rephrased|Reworded)[^:]*?:(.*?)(?:Overall|Added|Removed|$)', response, re.DOTALL | re.IGNORECASE)
        if rephrased_match:
            rephrased_text = rephrased_match.group(1).strip()
            if '-' in rephrased_text:
                rephrased_items = re.findall(r'-\s*(.*?)(?=\n-|\n\n|$)', rephrased_text, re.DOTALL)
                rephrased_content = [item.strip() for item in rephrased_items if item.strip()]
            else:
                rephrased_content = [rephrased_text]
        
        # Extract overall assessment
        assessment_match = re.search(r'(?:Overall|Assessment)[^:]*?:(.*?)(?:\n\n|$)', response, re.DOTALL | re.IGNORECASE)
        if assessment_match:
            improvement_assessment = assessment_match.group(1).strip()
        
        return {
            "added_content": added_content,
            "removed_content": removed_content,
            "rephrased_content": rephrased_content,
            "improvement_assessment": improvement_assessment,
            "full_comparison": response
        }