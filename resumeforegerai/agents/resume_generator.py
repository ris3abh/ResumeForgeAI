from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

from utils.file_utils import read_text_file, write_text_file, load_agent_config
from utils.openai_client import create_chat_openai
from utils.latex_utils import extract_latex_sections, modify_latex_section

class ResumeGeneratorAgent:
    """Agent for generating the final tailored resume.
    
    This agent combines all customized sections into a complete LaTeX resume
    and ensures coherent formatting and structure.
    """
    
    def __init__(self):
        """Initialize the resume generator agent."""
        # Load agent configuration
        self.config = load_agent_config("resume_generator")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = create_chat_openai(
            model_name=model_config["name"],
            temperature=model_config["temperature"]
        )
    
    def generate(self, 
                resume_file: str, 
                customized_sections: Dict[str, str], 
                compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final tailored resume.
        
        Args:
            resume_file: Path to the original resume file
            customized_sections: Dictionary of customized resume sections
            compliance_results: Results from the compliance verification
            
        Returns:
            Generated resume content and metadata
        """
        # Read the original resume
        original_resume = read_text_file(resume_file)
        
        # Extract all sections from the original resume
        original_sections = extract_latex_sections(original_resume)
        
        # Create an updated resume by replacing customized sections
        updated_resume = original_resume
        
        for section_name, customized_content in customized_sections.items():
            if section_name in original_sections:
                updated_resume = modify_latex_section(updated_resume, section_name, customized_content)
        
        # Create a prompt for final review and optimization
        prompt = self._create_final_review_prompt(updated_resume, compliance_results)
        
        # Get final review from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract final resume and modifications
        final_resume, modifications = self._extract_final_content(response.content, updated_resume)
        
        return {
            "original_resume": original_resume,
            "updated_resume": updated_resume,
            "final_resume": final_resume,
            "modifications": modifications,
            "raw_review": response.content
        }
    
    def save_resume(self, 
                   resume_content: str, 
                   output_file: str) -> bool:
        """Save the generated resume to a file.
        
        Args:
            resume_content: Content of the generated resume
            output_file: Path to save the resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            write_text_file(output_file, resume_content)
            return True
        except Exception as e:
            return False
    
    def _create_final_review_prompt(self, updated_resume: str, compliance_results: Dict[str, Any]) -> str:
        """Create a prompt for final resume review and optimization.
        
        Args:
            updated_resume: Combined resume with customized sections
            compliance_results: Results from the compliance verification
            
        Returns:
            Prompt for the LLM
        """
        # Extract information for the prompt
        missing_requirements = compliance_results.get("missing_requirements", [])
        missing_keywords = compliance_results.get("missing_keywords", [])
        compliance_score = compliance_results.get("compliance_score", 0)
        
        missing_req_text = "\n".join([f"- {req}" for req in missing_requirements])
        missing_kw_text = "\n".join([f"- {kw}" for kw in missing_keywords])
        
        return f"""
            {self.config['system_prompt']}

            I need you to review and finalize a customized resume. The resume has been tailored to match job requirements, but there may still be room for improvement.

            COMPLIANCE INFORMATION:
            - Current compliance score: {compliance_score}/100
            - Missing requirements: {missing_req_text if missing_req_text else "None"}
            - Missing keywords: {missing_kw_text if missing_kw_text else "None"}

            CURRENT RESUME:
            ```latex
            {updated_resume}
            ```

            Please review the resume and:
            1. Check for LaTeX formatting consistency and correctness
            2. Ensure coherent flow between sections
            3. Make any final adjustments to better address missing requirements or keywords
            4. Optimize the overall presentation and impact

            Your modifications should be minimal and focused on improving the resume's effectiveness. Maintain all LaTeX commands and formatting exactly as in the original.

            Respond with:
            1. The finalized LaTeX code for the complete resume
            2. A list of key modifications you made
            """
    
    def _extract_final_content(self, llm_response: str, updated_resume: str) -> tuple:
        """Extract final resume content and modifications from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            updated_resume: The previously updated resume
            
        Returns:
            Tuple of (final_resume, modifications)
        """
        # Look for LaTeX code blocks
        import re
        
        # Extract LaTeX content
        latex_match = re.search(r'```latex\s*([\s\S]*?)\s*```', llm_response)
        final_resume = latex_match.group(1) if latex_match else None
        
        # If no LaTeX block, try to extract without the language specifier
        if not final_resume:
            latex_match = re.search(r'```\s*([\s\S]*?)\s*```', llm_response)
            final_resume = latex_match.group(1) if latex_match else None
        
        # If still no LaTeX block, use the updated resume
        if not final_resume:
            final_resume = updated_resume
        
        # Extract modifications (everything after the LaTeX block)
        if latex_match:
            post_latex = llm_response[latex_match.end():]
            modifications_match = re.search(r'(?:modifications|changes|adjustments)(?::|^)([\s\S]*?)(?:```|$)', post_latex, re.IGNORECASE)
            modifications = modifications_match.group(1).strip() if modifications_match else post_latex.strip()
        else:
            modifications = "No explicit modifications listed."
        
        return final_resume, modifications