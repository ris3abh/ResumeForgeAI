from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic

from utils.file_utils import read_text_file, load_agent_config
from utils.latex_utils import analyze_latex_structure

class ResumeAnalyzerAgent:
    """Agent for analyzing LaTeX resume structure."""
    
    def __init__(self):
        """Initialize the resume analyzer agent."""
        # Load agent configuration
        self.config = load_agent_config("resume_analyzer")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = ChatAnthropic(
            model=model_config["name"],
            temperature=model_config["temperature"]
        )
    
    def analyze(self, resume_file: str) -> Dict[str, Any]:
        """Analyze a LaTeX resume file.
        
        Args:
            resume_file: Path to the LaTeX resume file
            
        Returns:
            Analysis results
        """
        # Read the resume file
        resume_content = read_text_file(resume_file)
        
        # Perform LaTeX structure analysis
        latex_analysis = analyze_latex_structure(resume_content)
        
        # Create a prompt for the LLM
        prompt = self._create_analysis_prompt(resume_content, latex_analysis)
        
        # Get analysis from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract structured information from the response
        detailed_analysis = self._extract_structured_analysis(response.content, latex_analysis)
        
        return detailed_analysis
    
    def _create_analysis_prompt(self, resume_content: str, latex_analysis: Dict[str, Any]) -> str:
        """Create a prompt for the LLM to analyze the resume.
        
        Args:
            resume_content: Raw content of the resume
            latex_analysis: Basic LaTeX structure analysis
            
        Returns:
            Prompt for the LLM
        """
        return f"""
{self.config['system_prompt']}

Please analyze the following LaTeX resume and provide a detailed breakdown of its structure and components:

```latex
{resume_content}
```

I've already performed some basic structural analysis:
- Document class: {latex_analysis.get('document_class', {}).get('name', 'Unknown')}
- Number of sections: {len(latex_analysis.get('sections', {}))}
- Number of packages: {len(latex_analysis.get('packages', []))}
- Number of custom commands: {len(latex_analysis.get('commands', []))}

Please provide your comprehensive analysis, including:
1. Overall structure of the resume
2. All sections identified and their purpose
3. LaTeX commands and environments used
4. Template style and formatting
5. Package imports and their purpose
6. Custom commands and their function

Format your response as a detailed technical analysis that can be used by other agents to understand how to modify this resume template.
"""
    
    def _extract_structured_analysis(self, llm_response: str, latex_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured information from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            latex_analysis: Basic LaTeX structure analysis
            
        Returns:
            Structured analysis results
        """
        # Combine programmatic analysis with LLM insights
        structured_analysis = {
            "raw_latex_analysis": latex_analysis,
            "llm_analysis": llm_response,
            "sections": [],
            "structure": {},
            "recommendations": []
        }
        
        # Extract section information
        for section_name, section_content in latex_analysis.get("sections", {}).items():
            structured_analysis["sections"].append({
                "name": section_name,
                "content_preview": section_content[:100] + "..." if len(section_content) > 100 else section_content,
                "length": len(section_content)
            })
        
        # Create a request for the LLM to extract structured information
        extraction_prompt = f"""
Based on the resume analysis you just provided, please extract the following structured information in a JSON format:
1. A list of all resume sections and their purpose
2. Key LaTeX commands that would need to be modified to customize this resume
3. The overall structure of the resume (hierarchy of sections)
4. Any recommendations for improving this resume template

Please format your response as valid JSON with these fields: sections, commands, structure, recommendations.
"""
        
        try:
            # Extract structured data using the LLM
            extraction_response = self.model.invoke([
                HumanMessage(content=extraction_prompt),
                AIMessage(content=llm_response)
            ])
            
            # Try to parse JSON from the response
            import json
            import re
            
            # Look for JSON block in the response
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', extraction_response.content)
            if json_match:
                json_str = json_match.group(1)
                try:
                    extracted_data = json.loads(json_str)
                    
                    # Update the structured analysis
                    for key, value in extracted_data.items():
                        structured_analysis[key] = value
                except json.JSONDecodeError:
                    # If JSON parsing fails, keep the raw LLM analysis
                    pass
        except Exception as e:
            # If extraction fails, continue with the analysis we have
            structured_analysis["extraction_error"] = str(e)
        
        return structured_analysis