from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

from utils.file_utils import read_text_file, load_agent_config
from utils.openai_client import create_chat_openai

class ComplianceAgent:
    """Agent for verifying that a resume meets job requirements.
    
    This agent checks if all key requirements and keywords from the job description
    are incorporated in the customized resume sections.
    """
    
    def __init__(self):
        """Initialize the compliance verification agent."""
        # Load agent configuration
        self.config = load_agent_config("compliance_agent")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = create_chat_openai(
            model_name=model_config["name"],
            temperature=model_config["temperature"]
        )
    
    def verify(self, 
               customized_sections: Dict[str, str], 
               job_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the customized resume sections meet job requirements.
        
        Args:
            customized_sections: Dictionary of customized resume sections
            job_analysis: Analysis of the job description
            
        Returns:
            Verification results with compliance score and suggestions
        """
        # Combine all customized sections for analysis
        combined_content = "\n\n".join([
            f"--- {section_name} ---\n{content}"
            for section_name, content in customized_sections.items()
        ])
        
        # Create a prompt for verification
        prompt = self._create_verification_prompt(combined_content, job_analysis)
        
        # Get verification from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract structured verification results
        verification_results = self._extract_structured_verification(response.content, job_analysis)
        
        return verification_results
    
    def suggest_improvements(self, 
                            verification_results: Dict[str, Any], 
                            customized_sections: Dict[str, str]) -> Dict[str, Any]:
        """Suggest improvements based on verification results.
        
        Args:
            verification_results: Results from the verification
            customized_sections: Dictionary of customized resume sections
            
        Returns:
            Improvement suggestions for each section
        """
        # Extract information for the prompt
        missing_requirements = verification_results.get("missing_requirements", [])
        missing_keywords = verification_results.get("missing_keywords", [])
        
        missing_req_text = "\n".join([f"- {req}" for req in missing_requirements])
        missing_kw_text = "\n".join([f"- {kw}" for kw in missing_keywords])
        
        prompt = f"""
{self.config.get('improvement_prompt', 'You are the Compliance Verification Agent. Your task is to suggest specific improvements for a resume to better address job requirements.')}

I've analyzed a customized resume and found the following gaps:

MISSING KEY REQUIREMENTS:
{missing_req_text if missing_req_text else "None"}

MISSING KEYWORDS:
{missing_kw_text if missing_kw_text else "None"}

For each of the following resume sections, please suggest specific improvements to address these gaps:

{chr(10).join([f"--- {section_name} ---\n{content[:200]}...\n" for section_name, content in customized_sections.items()])}

Please provide actionable suggestions for each section, explaining how to incorporate the missing requirements and keywords naturally and effectively.
"""
        
        # Get improvement suggestions from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract improvement suggestions by section
        suggestions_by_section = {}
        for section_name in customized_sections.keys():
            # Simple pattern matching to extract section-specific suggestions
            import re
            pattern = rf"(?:---\s*{re.escape(section_name)}\s*---|{re.escape(section_name)}:)(.*?)(?:---|$)"
            match = re.search(pattern, response.content, re.DOTALL | re.IGNORECASE)
            
            if match:
                suggestions_by_section[section_name] = match.group(1).strip()
            else:
                suggestions_by_section[section_name] = "No specific suggestions provided."
        
        return {
            "suggestions_by_section": suggestions_by_section,
            "raw_suggestions": response.content
        }
    
    def _create_verification_prompt(self, combined_content: str, job_analysis: Dict[str, Any]) -> str:
        """Create a prompt for compliance verification.
        
        Args:
            combined_content: Combined customized resume sections
            job_analysis: Analysis of the job description
            
        Returns:
            Prompt for the LLM
        """
        # Extract key information for the prompt
        key_requirements = job_analysis.get("structured_recommendations", {}).get("key_requirements", [])
        keywords = job_analysis.get("structured_recommendations", {}).get("keywords", [])
        
        requirements_text = "\n".join([f"- {req}" for req in key_requirements])
        keywords_text = "\n".join([f"- {kw}" for kw in keywords])
        
        return f"""
{self.config['system_prompt']}

I need you to verify that a customized resume meets the requirements of a job description.

KEY REQUIREMENTS FROM JOB DESCRIPTION:
{requirements_text}

IMPORTANT KEYWORDS FROM JOB DESCRIPTION:
{keywords_text}

CUSTOMIZED RESUME CONTENT:
{combined_content}

Please analyze the resume content and:
1. Check if each key requirement is effectively addressed in the resume
2. Verify if important keywords are incorporated naturally
3. Identify any missing requirements or keywords
4. Evaluate the overall compliance of the resume with the job requirements
5. Assign a compliance score from 0-100 based on how well the resume meets the requirements

Your analysis should be detailed and specific, identifying exactly what is missing or could be improved.
"""
    
    def _extract_structured_verification(self, llm_response: str, job_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured verification from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            job_analysis: Analysis of the job description
            
        Returns:
            Structured verification results
        """
        # Create a prompt to extract structured data
        extraction_prompt = f"""
            Based on your compliance verification response, please extract the following information in JSON format:
            1. addressed_requirements: List of key requirements that are effectively addressed in the resume
            2. missing_requirements: List of key requirements that are not effectively addressed
            3. incorporated_keywords: List of important keywords that are incorporated
            4. missing_keywords: List of important keywords that are missing
            5. compliance_score: A score from 0-100 representing overall compliance with job requirements
            6. improvement_areas: List of specific areas or sections that need improvement

            Please format your response ONLY as valid JSON with these fields.

            Your verification response:
            {llm_response}
            """
        
        try:
            # Get structured data from the LLM
            extraction_response = self.model.invoke([
                HumanMessage(content=extraction_prompt)
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
                    
                    # Process the structured data
                    all_requirements = job_analysis.get("structured_recommendations", {}).get("key_requirements", [])
                    all_keywords = job_analysis.get("structured_recommendations", {}).get("keywords", [])
                    
                    addressed_requirements = structured_data.get("addressed_requirements", [])
                    incorporated_keywords = structured_data.get("incorporated_keywords", [])
                    
                    # Calculate compliance metrics
                    req_compliance = len(addressed_requirements) / max(len(all_requirements), 1) * 100 if all_requirements else 100
                    kw_compliance = len(incorporated_keywords) / max(len(all_keywords), 1) * 100 if all_keywords else 100
                    
                    return {
                        "addressed_requirements": addressed_requirements,
                        "missing_requirements": structured_data.get("missing_requirements", []),
                        "incorporated_keywords": incorporated_keywords,
                        "missing_keywords": structured_data.get("missing_keywords", []),
                        "compliance_score": structured_data.get("compliance_score", (req_compliance + kw_compliance) / 2),
                        "improvement_areas": structured_data.get("improvement_areas", []),
                        "requirement_compliance_percentage": req_compliance,
                        "keyword_compliance_percentage": kw_compliance,
                        "raw_verification": llm_response
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, continue with a basic structure
                    pass
        except Exception as e:
            # If extraction fails, continue with a basic structure
            pass
        
        # Extract compliance score using regex (fallback)
        import re
        score_match = re.search(r'(?:compliance|overall)\s*score:?\s*(\d+)', llm_response, re.IGNORECASE)
        compliance_score = int(score_match.group(1)) if score_match else 50
        
        return {
            "addressed_requirements": [],
            "missing_requirements": [],
            "incorporated_keywords": [],
            "missing_keywords": [],
            "compliance_score": compliance_score,
            "improvement_areas": [],
            "requirement_compliance_percentage": 0,
            "keyword_compliance_percentage": 0,
            "raw_verification": llm_response
        }