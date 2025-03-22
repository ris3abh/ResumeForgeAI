from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

from utils.file_utils import read_text_file, load_agent_config
from utils.openai_client import create_chat_openai
from utils.latex_utils import extract_latex_sections

class SkillsAgent:
    """Agent for customizing the technical skills section of a resume.
    
    This agent reorganizes skills, adds relevant ones, and removes irrelevant ones
    based on the job description and requirements.
    """
    
    def __init__(self):
        """Initialize the skills customization agent."""
        # Load agent configuration
        self.config = load_agent_config("skills_agent")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = create_chat_openai(
            model_name=model_config["name"],
            temperature=model_config["temperature"]
        )
    
    def customize(self, 
                  resume_content: str, 
                  job_analysis: Dict[str, Any], 
                  resume_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Customize the skills section based on job requirements.
        
        Args:
            resume_content: Full content of the resume
            job_analysis: Analysis of the job description
            resume_analysis: Analysis of the resume structure
            
        Returns:
            Customized skills section and reasoning
        """
        # Extract the skills section
        sections = extract_latex_sections(resume_content)
        skills_section = sections.get("TECHNICAL SKILLS", "")
        
        if not skills_section:
            return {
                "error": "Could not find TECHNICAL SKILLS section in the resume",
                "customized_section": None,
                "reasoning": None
            }
        
        # Create a prompt for customization
        prompt = self._create_customization_prompt(skills_section, job_analysis, resume_analysis)
        
        # Get customization from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract customized section and reasoning
        customized_section, reasoning = self._extract_customized_content(response.content)
        
        return {
            "original_section": skills_section,
            "customized_section": customized_section,
            "reasoning": reasoning,
            "raw_customization": response.content
        }
    
    def refine(self, 
              customized_section: str, 
              validation_results: Dict[str, Any], 
              job_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Refine the customized section based on validation feedback.
        
        Args:
            customized_section: Previously customized section
            validation_results: Results from the LaTeX validator
            job_analysis: Analysis of the job description
            
        Returns:
            Refined customized section
        """
        # Create a prompt for refinement
        errors = validation_results.get("errors", [])
        warnings = validation_results.get("warnings", [])
        suggestions = validation_results.get("suggestions", [])
        
        error_text = "\n".join([f"- {error}" for error in errors])
        warning_text = "\n".join([f"- {warning}" for warning in warnings])
        suggestion_text = "\n".join([f"- {suggestion}" for suggestion in suggestions])
        
        prompt = f"""
            {self.config['system_prompt']}

            I need you to refine a customized technical skills section based on validation feedback. 

            CUSTOMIZED SECTION:
            ```latex
            {customized_section}
            ```

            VALIDATION FEEDBACK:
            Errors:
            {error_text if error_text else "None"}

            Warnings:
            {warning_text if warning_text else "None"}

            Suggestions:
            {suggestion_text if suggestion_text else "None"}

            Please refine the customized section to address all errors and warnings while maintaining the tailoring to the job requirements.

            Respond with the refined LaTeX code for the technical skills section.
            """
        
        # Get refinement from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract refined section
        refined_section, reasoning = self._extract_customized_content(response.content)
        
        return {
            "refined_section": refined_section,
            "reasoning": reasoning,
            "raw_refinement": response.content
        }
    
    def _create_customization_prompt(self, 
                                     skills_section: str, 
                                     job_analysis: Dict[str, Any], 
                                     resume_analysis: Dict[str, Any]) -> str:
        """Create a prompt for skills customization.
        
        Args:
            skills_section: Technical skills section content
            job_analysis: Analysis of the job description
            resume_analysis: Analysis of the resume structure
            
        Returns:
            Prompt for the LLM
        """
        # Extract key information for the prompt
        key_requirements = job_analysis.get("structured_recommendations", {}).get("key_requirements", [])
        technical_skills = job_analysis.get("structured_recommendations", {}).get("technical_skills", [])
        
        requirements_text = "\n".join([f"- {req}" for req in key_requirements])
        skills_text = "\n".join([f"- {skill}" for skill in technical_skills])
        
        return f"""
        {self.config['system_prompt']}

        I need you to customize the technical skills section of a resume to better match the following job requirements:

        KEY REQUIREMENTS:
        {requirements_text}

        TECHNICAL SKILLS NEEDED:
        {skills_text}

        CURRENT TECHNICAL SKILLS SECTION:
        ```latex
        {skills_section}
        ```

        Please customize this section to:
        1. Add any missing important skills from the job requirements (only if the candidate likely has them based on their experience)
        2. Highlight and prioritize skills that are most relevant to the job requirements
        3. De-emphasize or remove skills that are not relevant to this position
        4. Maintain proper LaTeX formatting
        5. Keep approximately the same layout and structure

        IMPORTANT: 
        - Maintain all LaTeX commands and formatting exactly as in the original
        - Only modify the content of each skill category, not the structure
        - Ensure the skills are organized in a logical manner
        - Be realistic - don't add skills the candidate doesn't likely have
        - Keep the same categories of skills as in the original

        Respond with:
        1. The customized LaTeX code for the technical skills section
        2. Your reasoning for the key changes made
        """
    
    def _extract_customized_content(self, llm_response: str) -> tuple:
        """Extract customized content and reasoning from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            
        Returns:
            Tuple of (customized_section, reasoning)
        """
        # Look for LaTeX code blocks
        import re
        
        # Extract LaTeX content
        latex_match = re.search(r'```latex\s*([\s\S]*?)\s*```', llm_response)
        customized_section = latex_match.group(1) if latex_match else None
        
        # If no LaTeX block, try to extract without the language specifier
        if not customized_section:
            latex_match = re.search(r'```\s*([\s\S]*?)\s*```', llm_response)
            customized_section = latex_match.group(1) if latex_match else None
        
        # If still no LaTeX block, use a simple heuristic to extract the section
        if not customized_section:
            lines = llm_response.split('\n')
            start_idx = None
            end_idx = None
            
            for i, line in enumerate(lines):
                if '\\resumeSubHeadingListStart' in line:
                    start_idx = i
                elif '\\resumeSubHeadingListEnd' in line and start_idx is not None:
                    end_idx = i
                    break
            
            if start_idx is not None and end_idx is not None:
                customized_section = '\n'.join(lines[start_idx:end_idx+1])
        
        # Extract reasoning (everything after the LaTeX block that's not another code block)
        if latex_match:
            post_latex = llm_response[latex_match.end():]
            reasoning_match = re.search(r'(?:reasoning|rationale|changes)(?::|^)([\s\S]*?)(?:```|$)', post_latex, re.IGNORECASE)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else post_latex.strip()
        else:
            reasoning = "No explicit reasoning provided."
        
        return customized_section, reasoning