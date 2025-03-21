from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic

from utils.file_utils import read_text_file, load_agent_config

class JobAnalyzerAgent:
    """Agent for analyzing job descriptions and providing resume tailoring recommendations."""
    
    def __init__(self):
        """Initialize the job analyzer agent."""
        # Load agent configuration
        self.config = load_agent_config("job_analyzer")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = ChatAnthropic(
            model=model_config["name"],
            temperature=model_config["temperature"]
        )
    
    def analyze(self, job_description_file: str, resume_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a job description and provide resume tailoring recommendations.
        
        Args:
            job_description_file: Path to the job description file
            resume_analysis: Analysis of the base resume
            
        Returns:
            Analysis results with tailoring recommendations
        """
        # Read the job description
        job_description = read_text_file(job_description_file)
        
        # Create a prompt for the LLM
        prompt = self._create_analysis_prompt(job_description, resume_analysis)
        
        # Get analysis from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract and structure the recommendations
        recommendations = self._structure_recommendations(response.content, resume_analysis)
        
        return {
            "job_description": job_description,
            "raw_analysis": response.content,
            "structured_recommendations": recommendations
        }
    
    def _create_analysis_prompt(self, job_description: str, resume_analysis: Dict[str, Any]) -> str:
        """Create a prompt for the LLM to analyze the job description.
        
        Args:
            job_description: Content of the job description
            resume_analysis: Analysis of the base resume
            
        Returns:
            Prompt for the LLM
        """
        # Extract sections from resume analysis to give context
        sections_info = "Resume sections:\n"
        for section in resume_analysis.get("sections", []):
            sections_info += f"- {section.get('name', 'Unnamed Section')}\n"
        
        return f"""
{self.config['system_prompt']}

Please analyze the following job description and provide specific recommendations for tailoring a resume:

JOB DESCRIPTION:
----------------
{job_description}

RESUME INFORMATION:
------------------
{sections_info}

{resume_analysis.get('llm_analysis', 'No detailed analysis available')}

Based on this information, please provide:
1. Key requirements and qualifications from the job description
2. Technical skills and tools required
3. Soft skills emphasized
4. Industry-specific terminology and keywords
5. Company values and culture indicators
6. Specific modifications to recommend for each resume section
7. Priority ranking of changes (high/medium/low importance)

Format your response as a detailed analysis with concrete, actionable recommendations for tailoring the resume to this specific job description.
"""
    
    def _structure_recommendations(self, llm_response: str, resume_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure the recommendations from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            resume_analysis: Analysis of the base resume
            
        Returns:
            Structured recommendations
        """
        # Create a prompt to extract structured data
        extraction_prompt = f"""
Based on your job description analysis, please extract the following structured information in JSON format:
1. key_requirements: List of key requirements from the job description
2. technical_skills: List of technical skills required
3. soft_skills: List of soft skills emphasized
4. keywords: Important keywords to include in the resume
5. section_recommendations: Object with recommendations for each resume section
6. prioritized_changes: List of recommended changes in priority order

Please format your response ONLY as valid JSON with these fields.
"""
        
        # Get structured data from the LLM
        try:
            extraction_response = self.model.invoke([
                HumanMessage(content=extraction_prompt + "\n\nYour analysis was:\n\n" + llm_response)
            ])
            
            # Try to parse JSON from the response
            import json
            import re
            
            # Look for JSON block in the response
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', extraction_response.content)
            if json_match:
                json_str = json_match.group(1)
                try:
                    structured_data = json.loads(json_str)
                    return structured_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a basic structure
                    pass
        except Exception as e:
            # If extraction fails, continue with a basic structure
            pass
        
        # Fallback: return basic structure with raw analysis
        return {
            "key_requirements": [],
            "technical_skills": [],
            "soft_skills": [],
            "keywords": [],
            "section_recommendations": {},
            "prioritized_changes": [],
            "raw_analysis": llm_response
        }