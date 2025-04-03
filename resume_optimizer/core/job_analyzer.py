"""Job analyzer for extracting key information from job descriptions."""

import re
from resume_optimizer.agents.base_agent import BaseOptimizerAgent
from resume_optimizer.utils.text_utils import format_analysis_for_prompt


class JobAnalyzer(BaseOptimizerAgent):
    """Agent for analyzing job descriptions."""
    
    def __init__(self, model=None):
        """Initialize the job analyzer agent.
        
        Args:
            model: Optional model to use
        """
        super().__init__(
            role_name="Job Description Analyzer",
            system_message_content=(
                "You are an expert at analyzing job descriptions and extracting key information. "
                "You can identify hard skills, soft skills, and keywords used in job descriptions "
                "and rank them according to their importance based on factors such as frequency, "
                "placement, emphasis, and whether they appear in the requirements section."
            ),
            model=model
        )
    
    def optimize(self, job_description, _=None):
        """Analyze a job description.
        
        Args:
            job_description: The job description text
            _: Unused parameter (for interface consistency)
            
        Returns:
            Dict containing analyzed job description data
        """
        analysis_prompt = (
            f"Analyze this job description and extract all important elements:\n\n{job_description}\n\n"
            f"Please provide your analysis in the following JSON-like format:\n"
            f"1. Hard Skills: List each hard skill with a relevance score (1-10)\n"
            f"2. Soft Skills: List each soft skill with a relevance score (1-10)\n"
            f"3. Keywords: List other important keywords with a relevance score (1-10)\n"
            f"4. Required vs Preferred: Categorize skills as required or preferred\n"
            f"5. Top 5 Most Critical Requirements: List the absolute must-haves"
        )
        
        response = self.process(analysis_prompt)
        analysis_results = self._parse_analysis_response(response)
        
        print("\n✅ Job Description Analysis Complete")
        print(f"Found {len(analysis_results.get('hard_skills', []))} hard skills, " 
              f"{len(analysis_results.get('soft_skills', []))} soft skills, and "
              f"{len(analysis_results.get('keywords', []))} key terms")
        
        return analysis_results
    
    def _parse_analysis_response(self, content):
        """Parse the job description analysis response to extract structured data.
        
        Args:
            content: Response content from the agent
            
        Returns:
            Dictionary with structured analysis data
        """
        result = {
            "hard_skills": [],
            "soft_skills": [],
            "keywords": [],
            "required": [],
            "preferred": [],
            "critical": []
        }
        
        # Extract Hard Skills
        hard_skills_match = re.search(r'Hard Skills:?(.*?)(?:Soft Skills:|$)', content, re.DOTALL)
        if hard_skills_match:
            skills_text = hard_skills_match.group(1).strip()
            for line in skills_text.split('\n'):
                if ':' in line or '-' in line:
                    parts = re.split(r':|(?<!\w)-(?!\w)', line, 1)
                    if len(parts) >= 2:
                        skill = parts[0].strip().strip('- ')
                        # Extract score if available
                        score_match = re.search(r'(\d+)(?:/10)?', parts[1])
                        score = int(score_match.group(1)) if score_match else 5
                        result["hard_skills"].append({"skill": skill, "score": score})
        
        # Extract Soft Skills
        soft_skills_match = re.search(r'Soft Skills:?(.*?)(?:Keywords:|$)', content, re.DOTALL)
        if soft_skills_match:
            skills_text = soft_skills_match.group(1).strip()
            for line in skills_text.split('\n'):
                if ':' in line or '-' in line:
                    parts = re.split(r':|(?<!\w)-(?!\w)', line, 1)
                    if len(parts) >= 2:
                        skill = parts[0].strip().strip('- ')
                        # Extract score if available
                        score_match = re.search(r'(\d+)(?:/10)?', parts[1])
                        score = int(score_match.group(1)) if score_match else 5
                        result["soft_skills"].append({"skill": skill, "score": score})
        
        # Extract Keywords
        keywords_match = re.search(r'Keywords:?(.*?)(?:Required vs Preferred:|$)', content, re.DOTALL)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            for line in keywords_text.split('\n'):
                if ':' in line or '-' in line:
                    parts = re.split(r':|(?<!\w)-(?!\w)', line, 1)
                    if len(parts) >= 2:
                        keyword = parts[0].strip().strip('- ')
                        # Extract score if available
                        score_match = re.search(r'(\d+)(?:/10)?', parts[1])
                        score = int(score_match.group(1)) if score_match else 5
                        result["keywords"].append({"keyword": keyword, "score": score})
        
        # Extract Required vs Preferred
        req_pref_match = re.search(r'Required vs Preferred:?(.*?)(?:Top 5|Critical Requirements:|$)', content, re.DOTALL)
        if req_pref_match:
            req_pref_text = req_pref_match.group(1).strip()
            
            # Extract Required
            required_match = re.search(r'Required:?(.*?)(?:Preferred:|$)', req_pref_text, re.DOTALL)
            if required_match:
                required_text = required_match.group(1).strip()
                for line in required_text.split('\n'):
                    if line.strip() and not line.strip().startswith("Required") and '-' in line:
                        skill = line.strip().strip('- ')
                        result["required"].append(skill)
            
            # Extract Preferred
            preferred_match = re.search(r'Preferred:?(.*?)$', req_pref_text, re.DOTALL)
            if preferred_match:
                preferred_text = preferred_match.group(1).strip()
                for line in preferred_text.split('\n'):
                    if line.strip() and not line.strip().startswith("Preferred") and '-' in line:
                        skill = line.strip().strip('- ')
                        result["preferred"].append(skill)
        
        # Extract Critical Requirements
        critical_match = re.search(r'(?:Top 5|Critical Requirements):?(.*?)$', content, re.DOTALL)
        if critical_match:
            critical_text = critical_match.group(1).strip()
            for line in critical_text.split('\n'):
                if line.strip() and ('-' in line or any(d in line for d in '123456789')):
                    skill = re.sub(r'^\d+\.\s*', '', line.strip().strip('- '))
                    if skill and not skill.startswith("Top") and not skill.startswith("Critical"):
                        result["critical"].append(skill)
        
        return result
    
    def format_analysis(self, analysis):
        """Format the job description analysis for inclusion in a prompt.
        
        Args:
            analysis: Dictionary containing analysis results
            
        Returns:
            Formatted string representation of the analysis
        """
        return format_analysis_for_prompt(analysis)