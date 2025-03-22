from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage

from utils.file_utils import read_text_file, load_agent_config
from utils.openai_client import create_chat_openai
from utils.latex_utils import analyze_latex_structure

class LaTeXValidatorAgent:
    """Agent for validating LaTeX format and structure.
    
    This agent ensures that customized LaTeX resume sections maintain proper
    formatting and are compatible with the original resume structure.
    """
    
    def __init__(self):
        """Initialize the LaTeX validator agent."""
        # Load agent configuration
        self.config = load_agent_config("latex_validator")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = create_chat_openai(
            model_name=model_config["name"],
            temperature=model_config["temperature"]
        )
    
    def validate(self, original_latex: str, modified_latex: str, section_name: str) -> Dict[str, Any]:
        """Validate a modified LaTeX section against the original.
        
        Args:
            original_latex: The original LaTeX content
            modified_latex: The modified LaTeX content
            section_name: Name of the section being validated
            
        Returns:
            Validation results with errors and suggestions
        """
        # Analyze both LaTeX structures
        original_analysis = analyze_latex_structure(original_latex)
        modified_analysis = analyze_latex_structure(modified_latex)
        
        # Create a prompt for validation
        prompt = self._create_validation_prompt(original_latex, modified_latex, original_analysis, modified_analysis, section_name)
        
        # Get validation from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract validation results
        validation_results = self._extract_structured_validation(response.content)
        
        return validation_results
    
    def _create_validation_prompt(self, 
                                 original_latex: str, 
                                 modified_latex: str, 
                                 original_analysis: Dict[str, Any], 
                                 modified_analysis: Dict[str, Any],
                                 section_name: str) -> str:
        """Create a prompt for LaTeX validation.
        
        Args:
            original_latex: The original LaTeX content
            modified_latex: The modified LaTeX content
            original_analysis: Analysis of the original LaTeX
            modified_analysis: Analysis of the modified LaTeX
            section_name: Name of the section being validated
            
        Returns:
            Prompt for the LLM
        """
        return f"""
            {self.config['system_prompt']}

            I need you to validate a modified LaTeX section to ensure it maintains proper formatting and is compatible with the original resume structure.

            SECTION NAME: {section_name}

            ORIGINAL LATEX:
            ```latex
            {original_latex}
            ```

            MODIFIED LATEX:
            ```latex
            {modified_latex}
            ```

            Please analyze both versions and provide:
            1. Is the modified LaTeX syntactically valid?
            2. Does it maintain the same LaTeX commands and environments as the original?
            3. Are there any formatting inconsistencies or errors?
            4. Would the modified LaTeX integrate seamlessly with the rest of the resume?
            5. Any specific suggestions for improving the modified LaTeX?

            Your validation should be detailed and specific, identifying line numbers or content where issues are found.
            """
    
    def _extract_structured_validation(self, llm_response: str) -> Dict[str, Any]:
        """Extract structured validation from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            
        Returns:
            Structured validation results
        """
        # Create a prompt to extract structured data
        extraction_prompt = f"""
            Based on your LaTeX validation response, please extract the following information in JSON format:
            1. is_valid: Boolean indicating if the modified LaTeX is valid
            2. errors: List of error messages with line numbers or content references
            3. warnings: List of warnings about potential issues
            4. suggestions: List of suggestions for improving the LaTeX
            5. can_proceed: Boolean indicating if the modified LaTeX can be used as is

            Please format your response ONLY as valid JSON with these fields.

            Your validation response:
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
                    return {
                        "is_valid": structured_data.get("is_valid", False),
                        "errors": structured_data.get("errors", []),
                        "warnings": structured_data.get("warnings", []),
                        "suggestions": structured_data.get("suggestions", []),
                        "can_proceed": structured_data.get("can_proceed", False),
                        "raw_validation": llm_response
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a basic structure
                    pass
        except Exception as e:
            # If extraction fails, continue with a basic structure
            pass
        
        # Simple pattern matching to determine validity (fallback)
        is_valid = "valid" in llm_response.lower() and not ("not valid" in llm_response.lower() or "invalid" in llm_response.lower())
        
        # Extract error messages using regex (fallback)
        import re
        errors = re.findall(r'error:?\s+([^\n.]+)', llm_response, re.IGNORECASE)
        warnings = re.findall(r'warning:?\s+([^\n.]+)', llm_response, re.IGNORECASE)
        suggestions = re.findall(r'suggest(?:ion)?:?\s+([^\n.]+)', llm_response, re.IGNORECASE)
        
        # Determine if we can proceed based on error count (fallback)
        can_proceed = is_valid and len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "can_proceed": can_proceed,
            "raw_validation": llm_response
        }