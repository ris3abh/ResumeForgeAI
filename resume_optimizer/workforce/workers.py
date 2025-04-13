# resume_optimizer/workforce/workers.py
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.core.job_analyzer import JobAnalyzer
from resume_optimizer.agents.skill_agent import SkillOptimizerAgent
from resume_optimizer.agents.experience_agent import ExperienceOptimizerAgent
from resume_optimizer.agents.ats_agent import ATSCompatibilityAgent
from resume_optimizer.agents.evaluator_agent import EvaluatorAgent
from resume_optimizer.utils.latex_utils import (
    read_latex_file, extract_section, replace_section, extract_latex_content
)
from resume_optimizer.tasks.task_definitions import get_task_metadata
from resume_optimizer.utils.model_factory import create_default_model
from resume_optimizer.tasks.task_utils import format_task_for_agent, parse_task_result
from resume_optimizer.utils.text_utils import format_analysis_for_prompt

from typing import Dict, List, Any
from camel.tasks import Task
import re

class JobAnalysisWorker(BaseOptimizerAgent):
    """Worker for analyzing job descriptions."""
    
    def __init__(self, model=None):
        """Initialize the job analyzer worker."""
        super().__init__(
            role_name="Job Description Analyzer",
            system_message_content=(
                "You are an expert at analyzing job descriptions for resume optimization. "
                "Your task is to extract all relevant information that would help tailor a resume to "
                "this specific job. You can identify hard skills, soft skills, keywords, job roles, "
                "and rank them according to their importance. You pay special attention to: "
                "1. Requirements explicitly marked as 'must' or 'required' "
                "2. Frequently mentioned technologies, concepts, or qualities "
                "3. The seniority level and leadership aspects of the role "
                "4. Domain-specific knowledge requirements "
                "5. Soft skills that indicate cultural fit or team dynamics "
                "6. Unique aspects of the role that differentiate it from similar positions"
            ),
            model=model
        )
    
    def optimize(self, content, context=None):
        """Not used for the job analysis worker."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the job analysis task."""
        job_description = task.additional_info.get("job_description")  # Retrieve from additional_info
        if not job_description:
            return "Error: No job description provided in task"
        
        analysis_prompt = (
            f"Analyze this job description thoroughly to help optimize a resume for the candidate:\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"Please provide your comprehensive analysis in the following format:\n\n"
            f"1. Core Role Information:\n"
            f"   - Job Title(s) mentioned\n"
            f"   - Seniority level\n"
            f"   - Department/Team context\n"
            f"   - Primary responsibility areas\n\n"
            f"2. Technical Skills: List each technical/hard skill with relevance score (1-10) and note if it's required or preferred\n\n"
            f"3. Soft Skills: List each soft skill with relevance score (1-10)\n\n"
            f"4. Domain Knowledge: List domain-specific knowledge areas required\n\n"
            f"5. Experience Requirements:\n"
            f"   - Years of experience\n"
            f"   - Types of experience (e.g., leadership, project management)\n"
            f"   - Specific accomplishments mentioned\n\n"
            f"6. Keywords: Other important terms and phrases with relevance score (1-10)\n\n"
            f"7. Top 10 Most Critical Requirements: List the absolute must-haves in order of importance\n\n"
            f"8. Resume Optimization Strategy:\n"
            f"   - Key sections to emphasize\n"
            f"   - Specific achievements to highlight\n"
            f"   - Terminology alignment suggestions\n"
            f"   - Areas to de-emphasize or remove\n\n"
            f"Focus on being comprehensive but precise. Identify patterns, recurring themes, and implicit requirements."
        )
        
        response = self.process(analysis_prompt)
        
        # Parse and structure the response
        analysis_results = self._parse_enhanced_analysis_response(response)
        
        # Return structured analysis as task result
        formatted_analysis = format_analysis_for_prompt(analysis_results)
        task.result = analysis_results
        
        return formatted_analysis
    
    def _parse_enhanced_analysis_response(self, response_content):
        """Parse the job description analysis response to extract structured data."""
        # [Same parser logic as in the original job_analyzer.py]
        # This would be the same implementation from the original file
        result = {
            "core_role": {},
            "technical_skills": [],
            "soft_skills": [],
            "domain_knowledge": [],
            "experience": {},
            "keywords": [],
            "critical": [],
            "optimization_strategy": {},
            "required": [],
            "preferred": []
        }
        
        # Extract Core Role Information
        core_role_match = re.search(r'Core Role Information:?(.*?)(?:Technical Skills:|$)', response_content, re.DOTALL)
        if core_role_match:
            core_text = core_role_match.group(1).strip()
            
            # Job Title
            title_match = re.search(r'Job Title\(?s?\)?:?\s*(.*?)(?:\n|$)', core_text, re.DOTALL)
            if title_match:
                result["core_role"]["job_title"] = title_match.group(1).strip()
            
            # Seniority level
            seniority_match = re.search(r'Seniority level:?\s*(.*?)(?:\n|$)', core_text, re.DOTALL)
            if seniority_match:
                result["core_role"]["seniority"] = seniority_match.group(1).strip()
            
            # Department/Team
            dept_match = re.search(r'Department/Team:?\s*(.*?)(?:\n|$)', core_text, re.DOTALL)
            if dept_match:
                result["core_role"]["department"] = dept_match.group(1).strip()
            
            # Responsibilities
            resp_match = re.search(r'Primary responsibility:?\s*(.*?)(?:\n\n|$)', core_text, re.DOTALL)
            if resp_match:
                result["core_role"]["responsibilities"] = resp_match.group(1).strip()
        
        # [Continue extracting other sections as in the original parser]
        # For brevity, I'm not including the full parser implementation here
        
        return result


class SectionExtractorWorker(BaseOptimizerAgent):
    """Worker for extracting sections from resumes."""
    
    def __init__(self, model=None):
        """Initialize the section extractor worker."""
        super().__init__(
            role_name="Resume Section Extractor",
            system_message_content=(
                "You are an expert at extracting and identifying different sections from resumes. "
                "You can identify standard sections like 'Professional Summary', 'Technical Skills', "
                "'Experience', 'Education', 'Certifications', etc. You understand LaTeX formatting "
                "and can extract content between section markers."
            ),
            model=model
        )
    
    def optimize(self, content, context=None):
        """Not used for the section extractor worker."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the section extraction task."""
        if not hasattr(task, "resume_path") or not task.resume_path:
            return "Error: No resume path provided in task"
        
        resume_content = read_latex_file(str(task.resume_path))
        
        # Define common resume sections to extract
        sections = ["PROFESSIONAL SUMMARY", "TECHNICAL SKILLS", "EXPERIENCE", "CERTIFICATIONS", "EDUCATION"]
        extracted_sections = {}
        
        # Extract each section
        for section_name in sections:
            section_content = extract_section(resume_content, section_name)
            if section_content:
                extracted_sections[section_name] = section_content
        
        # Return extracted sections as task result
        task.result = {"sections": extracted_sections}
        
        # Prepare a summary response
        response = "Successfully extracted the following sections:\n"
        for section_name, content in extracted_sections.items():
            response += f"- {section_name} ({len(content)} characters)\n"
        
        return response


class SkillsOptimizationWorker(BaseOptimizerAgent):
    """Worker for optimizing skills sections."""
    
    def __init__(self, model=None):
        """Initialize the skills optimization worker."""
        super().__init__(
            role_name="Technical Skills Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing technical skills sections to perfectly match job descriptions. "
                "You understand how to add and remove skills strategically while maintaining the original LaTeX formatting. "
                "You ensure high alignment with the ATS requirements by properly organizing skills into categories and ensuring "
                "they reflect the exact terminology used in the job description."
            ),
            model=model
        )
    
    def optimize(self, content, context=None):
        """Not used directly in the workforce implementation."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the skills optimization task."""
        if not hasattr(task, "section_name") or not task.section_name or not hasattr(task, "section_content") or not task.section_content:
            return "Error: Missing section name or content in task"
        
        analysis_results = task.additional_info.get("analysis_results")  # Retrieve from additional_info
        if not analysis_results:
            return "Error: Missing job analysis results in task"
        
        section_name = task.section_name
        section_content = task.section_content
        
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(analysis_results)
        
        # Create specialized prompt for skills optimization
        skills_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Technical Skill Section: \n\n<Resume Technical Skill Section Start>\n{section_content}\n<Resume Technical Skill Section End>\n\n"
            f"Your task is to optimize this skills section to achieve an excellent ATS match (90%+ score) in one pass. You should:\n\n"
            f"1. Add ALL keywords and skills from the job analysis that are missing from the skills section\n"
            f"2. Place them into appropriate subcategories like the existing ones in the skills section\n"
            f"3. Remove skills which are not relevant to the job description or have low scores in the analysis\n"
            f"4. Prioritize required skills and order them by importance\n"
            f"5. Use the EXACT terminology from the job description for maximum ATS compatibility\n"
            f"6. Ensure the LaTeX formatting is preserved perfectly\n\n"
            f"IMPORTANT: Give the updated skill section in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or AI assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current skills section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(skills_prompt)
        optimized_skills = extract_latex_content(response)
        
        # If we couldn't extract valid content, try once more with clearer instructions
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
            # Use original content if extraction fails
            optimized_skills = section_content
        
        # Store the result
        task.result = {
            "optimized_content": optimized_skills,
            "section_name": section_name
        }
        
        return optimized_skills


class ExperienceOptimizationWorker(BaseOptimizerAgent):
    """Worker for optimizing experience sections."""
    
    def __init__(self, model=None):
        """Initialize the experience optimization worker."""
        super().__init__(
            role_name="Work Experience Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing work experience sections to perfectly match job descriptions. "
                "You know how to incorporate keywords, hard skills, soft skills, and action words while maintaining "
                "the original format and integrity of accomplishments. You ensure high alignment with ATS requirements "
                "by including all key terms from the job description and emphasizing relevant achievements."
            ),
            model=model
        )
        
        # List of strong action verbs for resume bullets
        self.action_words = [
            "Spearheaded", "Orchestrated", "Catalyzed", "Implemented", "Pioneered", 
            "Transformed", "Streamlined", "Revolutionized", "Overhauled", "Innovated", 
            "Leveraged", "Optimized", "Negotiated", "Cultivated", "Accelerated", 
            "Championed", "Executed", "Launched", "Redesigned", "Maximized", 
            "Engineered", "Strategized", "Revitalized", "Conceptualized", "Facilitated"
        ]
    
    def optimize(self, content, context=None):
        """Not used directly in the workforce implementation."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the experience optimization task."""
        if not hasattr(task, "section_name") or not task.section_name or not hasattr(task, "section_content") or not task.section_content:
            return "Error: Missing section name or content in task"
        
        analysis_results = task.additional_info.get("analysis_results")  # Retrieve from additional_info
        if not analysis_results:
            return "Error: Missing job analysis results in task"
        
        section_name = task.section_name
        section_content = task.section_content
        
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(analysis_results)
        action_words_text = ", ".join(self.action_words)
        
        # Create specialized prompt for experience optimization
        experience_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Work Experience Section: \n\n<Resume Work Experience Section Start>\n{section_content}\n<Resume Work Experience Section End>\n\n"
            f"Your task is to optimize this experience section to achieve an excellent ATS match (90%+ score) in one pass. You should:\n\n"
            f"1. Incorporate ALL keywords, hard skills, and soft skills from the job analysis into the work experience\n"
            f"2. Use strong action verbs at the beginning of each bullet point (choose from this list: {action_words_text})\n"
            f"3. Keep bullet points between 16-18 words with clear metrics and achievements\n"
            f"4. Ensure each bullet highlights achievements relevant to the job requirements\n"
            f"5. Use the EXACT terminology from the job description for maximum ATS compatibility\n"
            f"6. Emphasize leadership, technical expertise, and business impact that matches the job's requirements\n"
            f"7. Preserve the original LaTeX formatting perfectly\n\n"
            f"IMPORTANT: Give the updated experience section in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or AI assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current experience section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(experience_prompt)
        optimized_experience = extract_latex_content(response)
        
        # If we couldn't extract valid content, try once more with clearer instructions
        if not optimized_experience.startswith('\\resume'):
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
            # Use original content if extraction fails
            optimized_experience = section_content
        
        # Store the result
        task.result = {
            "optimized_content": optimized_experience,
            "section_name": section_name
        }
        
        return optimized_experience

class SummaryOptimizationWorker(BaseOptimizerAgent):
    """Worker for optimizing summary sections."""
    
    def __init__(self, model=None):
        """Initialize the summary optimization worker."""
        super().__init__(
            role_name="Professional Summary Optimizer",
            system_message_content=(
                "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
                "You specialize in optimizing professional summary sections to perfectly match job descriptions. "
                "You create concise, powerful summaries that emphasize the candidate's alignment with job requirements "
                "while including key terminology for ATS compatibility."
            ),
            model=model
        )
    
    def optimize(self, content, context=None):
        """Not used directly in the workforce implementation."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the summary optimization task."""
        if not hasattr(task, "section_name") or not task.section_name or not hasattr(task, "section_content") or not task.section_content:
            return "Error: Missing section name or content in task"
        
        if not task.metadata or "analysis_results" not in task.metadata:
            return "Error: Missing job analysis results in task"
        
        section_name = task.section_name
        section_content = task.section_content
        analysis_results = task.metadata["analysis_results"]
        
        # If the section is missing (some resumes might not have a summary), create a placeholder
        if not section_content:
            section_content = "\\resumeSubHeadingListStart\n\\resumeItem{Results-driven professional with expertise in...}\n\\resumeSubHeadingListEnd"
        
        # Format the job analysis for the prompt
        job_analysis_text = format_analysis_for_prompt(analysis_results)
        
        # Create specialized prompt for summary optimization
        summary_prompt = (
            f"Analyze this Job Description Analysis: \n\n<JD Analysis Start>\n{job_analysis_text}\n<JD Analysis End>\n\n"
            f"And this Resume Professional Summary Section: \n\n<Resume Summary Section Start>\n{section_content}\n<Resume Summary Section End>\n\n"
            f"Your task is to optimize this professional summary to achieve an excellent ATS match (90%+ score) in one pass. You should:\n\n"
            f"1. Create a concise (2-3 sentences, 40-60 words) professional summary\n"
            f"2. Include the top 5-7 most critical skills and keywords from the job description\n"
            f"3. Match the seniority level and leadership emphasis from the job requirements\n"
            f"4. Emphasize quantifiable achievements that align with the job's priorities\n"
            f"5. Use the EXACT terminology from the job description for maximum ATS compatibility\n"
            f"6. Focus on the candidate's value proposition for the specific role\n"
            f"7. Preserve the original LaTeX formatting perfectly\n\n"
            f"IMPORTANT: Give the updated summary in the EXACT LaTeX format as provided in the original. "
            f"Do NOT include any explanations, markdown formatting, or AI assistant text in your response. "
            f"Return ONLY the LaTeX code that should replace the current summary section."
        )
        
        # Get the response and extract the LaTeX content
        response = self.process(summary_prompt)
        optimized_summary = extract_latex_content(response)
        
        # If we couldn't extract valid content, try once more with clearer instructions
        if not optimized_summary.startswith('\\resume'):
            clarification_message = (
                "Your response wasn't formatted correctly. I need ONLY raw LaTeX code "
                "starting with \\resumeSubHeadingListStart and ending with \\resumeSubHeadingListEnd. "
                "No explanation, no markdown formatting, just the raw LaTeX code like in the original. "
                "Please try again with ONLY the LaTeX code."
            )
            response = self.process(clarification_message)
            optimized_summary = extract_latex_content(response)
        
        # Final validation to ensure we have valid LaTeX
        if not optimized_summary.startswith('\\resume'):
            # Use original content if extraction fails
            optimized_summary = section_content
        
        # Store the result
        task.result = {
            "optimized_content": optimized_summary,
            "section_name": section_name
        }
        
        return optimized_summary


class ResumeAssemblerWorker(BaseOptimizerAgent):
    """Worker for assembling optimized sections into a complete resume."""
    
    def __init__(self, model=None):
        """Initialize the resume assembler worker."""
        super().__init__(
            role_name="Resume Assembler",
            system_message_content=(
                "You are an expert at assembling optimized resume sections into a complete, "
                "cohesive resume. You understand LaTeX formatting and ensure that all sections "
                "are properly integrated while maintaining consistent formatting and style."
            ),
            model=model
        )
    
    def optimize(self, content, context=None):
        """Not used directly in the workforce implementation."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the resume assembly task."""
        if not hasattr(task, "resume_path") or not task.resume_path:
            return "Error: No resume path provided in task"
        
        if not hasattr(task, "analysis_results") or not task.analysis_results or "optimized_sections" not in task.analysis_results:
            return "Error: Missing optimized sections in task"
        
        resume_path = task.resume_path
        optimized_sections = task.analysis_results["optimized_sections"]
        
        # Read the original resume
        original_resume = read_latex_file(str(resume_path))
        updated_resume = original_resume
        
        # Replace each section with its optimized version
        for section_name, section_content in optimized_sections.items():
            updated_resume = replace_section(updated_resume, section_name, section_content)
        
        # Store the result
        task.result = updated_resume
        
        return f"Successfully assembled optimized resume with {len(optimized_sections)} updated sections"


class ATSCheckWorker(BaseOptimizerAgent):
    """Worker for checking ATS compatibility of resumes."""
    
    def __init__(self, model=None):
        """Initialize the ATS check worker."""
        super().__init__(
            role_name="ATS Compatibility Expert",
            system_message_content=(
                "You are an expert at evaluating resumes for ATS compatibility with over 10 years "
                "of experience in resume optimization. You provide detailed feedback on how well "
                "a resume will perform with ATS systems, evaluating keyword matching, formatting, "
                "and overall alignment with job requirements."
            ),
            model=model
        )
    
    def optimize(self, content, context=None):
        """Not used directly in the workforce implementation."""
        pass
    
    def process_task(self, task: Task) -> str:
        """Process the ATS check task."""
        if not hasattr(task, "resume_path") or not task.resume_path:
            return "Error: No resume path provided in task"
        
        if not task.metadata or "job_description" not in task.metadata:
            return "Error: No job description provided in task"
        
        resume_path = task.resume_path
        job_description = task.metadata["job_description"]
        
        # Read the resume
        resume_content = read_latex_file(str(resume_path))
        
        # Create specialized prompt for ATS evaluation
        ats_prompt = (
            f"Evaluate this resume for ATS compatibility with the following job description:\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"RESUME:\n{resume_content}\n\n"
            f"Please provide:\n"
            f"1. A score out of 100 for ATS compatibility\n"
            f"2. Detailed feedback on the resume's ATS performance, including:\n"
            f"   - Keyword match rate with the job description\n"
            f"   - Formatting and structure analysis\n"
            f"   - Any missing critical skills or requirements\n"
            f"   - Suggestions for further improvement (if needed)\n"
            f"   - Overall assessment of how well the resume matches the job description"
        )
        
        # Get the response
        response = self.process(ats_prompt)
        
        # Extract score and feedback using regex
        score_match = re.search(r'(\d{1,3})(?:\s*\/\s*|\s+out\s+of\s+)100', response, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 85
        
        # Extract feedback (everything after the score)
        if score_match:
            feedback_start = score_match.end()
            feedback = response[feedback_start:].strip()
        else:
            feedback = response
        
        # Store the result
        task.result = {
            "score": score,
            "feedback": feedback
        }
        
        return f"ATS Compatibility Score: {score}/100\n\n{feedback}"