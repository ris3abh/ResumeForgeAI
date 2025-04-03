"""Utilities for handling LaTeX documents."""

import re
from pathlib import Path


def read_latex_file(file_path: str) -> str:
    """Read a LaTeX file and return its content.
    
    Args:
        file_path: Path to the LaTeX file
        
    Returns:
        The content of the file as a string
    """
    with open(file_path, 'r') as file:
        return file.read()


def save_latex_file(content: str, output_path: str) -> None:
    """Save content to a LaTeX file.
    
    Args:
        content: The LaTeX content to save
        output_path: Path where the file will be saved
    """
    with open(output_path, 'w') as file:
        file.write(content)


def extract_section(latex_content: str, section_name: str) -> str:
    """Extract a specific section from LaTeX content.
    
    Args:
        latex_content: The full LaTeX document content
        section_name: The name of the section to extract
        
    Returns:
        The content of the extracted section
    """
    pattern = rf"\\section{{{section_name}}}(.*?)(?:\\section{{|\\end{{document}})"
    match = re.search(pattern, latex_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def replace_section(latex_content: str, section_name: str, new_content: str) -> str:
    """Replace a section in the LaTeX document with new content.
    
    Args:
        latex_content: The full LaTeX document content
        section_name: The name of the section to replace
        new_content: The new content for the section
        
    Returns:
        The updated LaTeX document content
    """
    pattern = rf"(\\section{{{section_name}}})(.*?)(?=\\section{{|\\end{{document}})"
    
    def replacement_func(match):
        return match.group(1) + new_content + "\n\n"
    
    return re.sub(pattern, replacement_func, latex_content, flags=re.DOTALL)


def extract_latex_content(content: str) -> str:
    """Extract LaTeX content from an AI response.
    
    Args:
        content: The AI response containing LaTeX code
        
    Returns:
        The extracted and cleaned LaTeX content
    """
    # Look for content in code blocks with latex tag
    code_block_match = re.search(r'```(?:latex)?\s*(.*?)\s*```', content, flags=re.DOTALL)
    if code_block_match:
        latex_content = code_block_match.group(1).strip()
        # Further clean the extracted LaTeX
        return clean_latex_content(latex_content)
    
    # If no code blocks, look for content after "Solution:" or similar
    solution_match = re.search(r'Solution:(.*?)(?:Next request|$)', content, flags=re.DOTALL)
    if solution_match:
        latex_content = solution_match.group(1).strip()
        return clean_latex_content(latex_content)
    
    # Look for content after other common prefixes
    content_match = re.search(r'(?:Here is the optimized|Optimized content:|Here\'s the optimized)(.*?)(?:Next request|$)', content, flags=re.DOTALL|re.IGNORECASE)
    if content_match:
        latex_content = content_match.group(1).strip()
        return clean_latex_content(latex_content)
    
    # Fallback - just clean the entire content
    return clean_latex_content(content)


def clean_latex_content(content: str) -> str:
    """Clean LaTeX content by removing non-LaTeX elements.
    
    Args:
        content: The LaTeX content to clean
        
    Returns:
        The cleaned LaTeX content
    """
    # Remove any markdown code block markers
    content = re.sub(r'```latex|```', '', content)
    
    # Remove any "I must reiterate..." or similar AI explanations
    content = re.sub(r'I must reiterate[^\\]*?(?=\\|$)', '', content, flags=re.DOTALL)
    
    # Remove any "Thank you for confirming..." or similar AI closings
    content = re.sub(r'Thank you for[^\\]*?(?=\\|$)', '', content, flags=re.DOTALL)
    
    # Keep only LaTeX commands and content between \resumeSubHeadingListStart and \resumeSubHeadingListEnd
    latex_section_match = re.search(r'(\\resumeSubHeadingListStart.*?\\resumeSubHeadingListEnd)', content, flags=re.DOTALL)
    if latex_section_match:
        return latex_section_match.group(1).strip()
    
    # Or keep content with LaTeX commands like \resumeItem, \resumeSubheading
    latex_commands_match = re.search(r'(\\resume.*)', content, flags=re.DOTALL)
    if latex_commands_match:
        return latex_commands_match.group(1).strip()
    
    # Remove any remaining AI assistant text like "Here's the formatted..." 
    content = re.sub(r'Here\'s the [^\n]*\n', '', content)
    content = re.sub(r'I\'ve [^\n]*\n', '', content)
    
    # If there's a section* command, convert it to the proper format
    content = re.sub(r'\\section\*{([^}]+)}', r'\\resumeSubHeadingListStart', content)
    
    # Ensure content ends with proper closing if it contains resumeSubHeadingListStart
    if '\\resumeSubHeadingListStart' in content and '\\resumeSubHeadingListEnd' not in content:
        content += '\n\\resumeSubHeadingListEnd'
    
    return content.strip()