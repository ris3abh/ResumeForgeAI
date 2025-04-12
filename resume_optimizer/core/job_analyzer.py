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
                "You are an expert at analyzing job descriptions for resume optimization. "
                "Your task is to extract all relevant information that would help tailor a resume to "
                "this specific job. You can identify hard skills, soft skills, keywords, job roles, technical keywords "
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
    
    def optimize(self, job_description, _=None):
        """Analyze a job description.
        
        Args:
            job_description: The job description text
            _: Unused parameter (for interface consistency)
            
        Returns:
            Dict containing analyzed job description data
        """
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
        analysis_results = self._parse_enhanced_analysis_response(response)
        
        print("\n✅ Job Description Analysis Complete")
        
        # Print a summary of what was found
        print(f"Found {len(analysis_results.get('technical_skills', []))} technical skills, " 
              f"{len(analysis_results.get('soft_skills', []))} soft skills, and "
              f"{len(analysis_results.get('keywords', []))} keywords")
        print(f"Top 20 critical requirements: {', '.join([c for c in analysis_results.get('critical', [])[:20]])}...")
        
        return analysis_results
    
    def _parse_enhanced_analysis_response(self, response_content):
        """Parse the job description analysis response to extract structured data.
        
        This enhanced parser extracts more detailed information from the analysis.
        
        Args:
            response_content: Response content from the agent
            
        Returns:
            Dictionary with structured analysis data
        """
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
        
        # Extract Technical Skills
        tech_skills_match = re.search(r'Technical Skills:?(.*?)(?:Soft Skills:|$)', response_content, re.DOTALL)
        if tech_skills_match:
            skills_text = tech_skills_match.group(1).strip()
            for line in skills_text.split('\n'):
                if ':' in line or '-' in line:
                    parts = re.split(r':|(?<!\w)-(?!\w)', line, 1)
                    if len(parts) >= 2:
                        skill = parts[0].strip().strip('- ')
                        # Extract score if available
                        score_match = re.search(r'(\d+)(?:/10)?', parts[1])
                        score = int(score_match.group(1)) if score_match else 5
                        
                        # Check if required or preferred
                        is_required = "required" in parts[1].lower()
                        is_preferred = "preferred" in parts[1].lower() and not is_required
                        
                        skill_info = {"skill": skill, "score": score}
                        result["technical_skills"].append(skill_info)
                        
                        if is_required:
                            result["required"].append(skill)
                        elif is_preferred:
                            result["preferred"].append(skill)
        
        # Extract Soft Skills
        soft_skills_match = re.search(r'Soft Skills:?(.*?)(?:Domain Knowledge:|$)', response_content, re.DOTALL)
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
        
        # Extract Domain Knowledge
        domain_match = re.search(r'Domain Knowledge:?(.*?)(?:Experience Requirements:|$)', response_content, re.DOTALL)
        if domain_match:
            domain_text = domain_match.group(1).strip()
            for line in domain_text.split('\n'):
                if line.strip() and ('-' in line or ':' in line):
                    domain = re.sub(r'^[- ]*', '', line).strip()
                    result["domain_knowledge"].append(domain)
        
        # Extract Experience Requirements
        exp_match = re.search(r'Experience Requirements:?(.*?)(?:Keywords:|$)', response_content, re.DOTALL)
        if exp_match:
            exp_text = exp_match.group(1).strip()
            
            # Years of experience
            years_match = re.search(r'Years of experience:?\s*(.*?)(?:\n|$)', exp_text)
            if years_match:
                result["experience"]["years"] = years_match.group(1).strip()
            
            # Types of experience
            types_match = re.search(r'Types of experience:?\s*(.*?)(?:\n\n|$)', exp_text, re.DOTALL)
            if types_match:
                types_text = types_match.group(1).strip()
                types = [t.strip() for t in re.split(r'[,;]|\n-', types_text) if t.strip()]
                result["experience"]["types"] = types
            
            # Accomplishments
            accomp_match = re.search(r'Specific accomplishments:?\s*(.*?)(?:\n\n|$)', exp_text, re.DOTALL)
            if accomp_match:
                accomp_text = accomp_match.group(1).strip()
                accomplishments = [a.strip() for a in re.split(r'\n-', accomp_text) if a.strip()]
                result["experience"]["accomplishments"] = accomplishments
        
        # Extract Keywords
        keywords_match = re.search(r'Keywords:?(.*?)(?:Top 10|Critical Requirements:|$)', response_content, re.DOTALL)
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
        
        # Extract Critical Requirements
        critical_match = re.search(r'(?:Top 10|Critical Requirements):?(.*?)(?:Resume Optimization Strategy:|$)', response_content, re.DOTALL)
        if critical_match:
            critical_text = critical_match.group(1).strip()
            for line in critical_text.split('\n'):
                if line.strip() and ('-' in line or any(d in line for d in '0123456789')):
                    # Remove numbers and bullet points
                    req = re.sub(r'^\d+\.?\s*|-\s*', '', line.strip())
                    if req and not req.startswith("Top") and not req.startswith("Critical"):
                        result["critical"].append(req)
        
        # Extract Optimization Strategy
        strategy_match = re.search(r'Resume Optimization Strategy:?(.*?)$', response_content, re.DOTALL)
        if strategy_match:
            strategy_text = strategy_match.group(1).strip()
            
            # Sections to emphasize
            sections_match = re.search(r'Key sections:?\s*(.*?)(?:\n\n|$)', strategy_text, re.DOTALL)
            if sections_match:
                sections_text = sections_match.group(1).strip()
                sections = [s.strip() for s in re.split(r'[,;]|\n-', sections_text) if s.strip()]
                result["optimization_strategy"]["sections"] = sections
            
            # Achievements
            achievements_match = re.search(r'Specific achievements:?\s*(.*?)(?:\n\n|$)', strategy_text, re.DOTALL)
            if achievements_match:
                achievements_text = achievements_match.group(1).strip()
                achievements = [a.strip() for a in re.split(r'[,;]|\n-', achievements_text) if a.strip()]
                result["optimization_strategy"]["achievements"] = achievements
            
            # Terminology
            term_match = re.search(r'Terminology alignment:?\s*(.*?)(?:\n\n|$)', strategy_text, re.DOTALL)
            if term_match:
                term_text = term_match.group(1).strip()
                terms = [t.strip() for t in re.split(r'[,;]|\n-', term_text) if t.strip()]
                result["optimization_strategy"]["terminology"] = terms
            
            # Areas to de-emphasize
            deemph_match = re.search(r'Areas to de-emphasize:?\s*(.*?)(?:\n\n|$)', strategy_text, re.DOTALL)
            if deemph_match:
                deemph_text = deemph_match.group(1).strip()
                deemph = [d.strip() for d in re.split(r'[,;]|\n-', deemph_text) if d.strip()]
                result["optimization_strategy"]["de-emphasize"] = deemph
        
        return result
    
    def format_analysis(self, analysis):
        """Format the job description analysis for inclusion in a prompt.
        
        Args:
            analysis: Dictionary containing analysis results
            
        Returns:
            Formatted string representation of the analysis
        """
        return format_analysis_for_prompt(analysis)