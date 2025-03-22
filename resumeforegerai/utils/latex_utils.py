def modify_latex_section(latex_content: str, section_name: str, new_content: str) -> str:
    """Modify a specific section in a LaTeX document.
    
    Args:
        latex_content: The content of the LaTeX file
        section_name: The name of the section to modify
        new_content: The new content for the section
        
    Returns:
        The modified LaTeX content
    """
    # Pattern to find the section and its content
    pattern = rf'(\\section\{{{re.escape(section_name)}\}}).*?((?=\\section\{{|\\end\{{document\}}))'
    
    # Replace the section content
    return re.sub(pattern, f'\\1\n{new_content}\n', latex_content, flags=re.DOTALL)

def combine_latex_sections(original_latex: str, customized_sections: Dict[str, str]) -> str:
    """Combine the original LaTeX document with customized sections.
    
    Args:
        original_latex: The original LaTeX content
        customized_sections: Dictionary mapping section names to customized content
        
    Returns:
        The combined LaTeX content
    """
    # Start with the original LaTeX
    combined_latex = original_latex
    
    # Replace each section with its customized version
    for section_name, customized_content in customized_sections.items():
        if customized_content:
            combined_latex = modify_latex_section(combined_latex, section_name, customized_content)
    
    return combined_latex

def extract_section_content(latex_content: str, section_name: str) -> str:
    """Extract the content of a specific section from a LaTeX document.
    
    Args:
        latex_content: The content of the LaTeX file
        section_name: The name of the section to extract
        
    Returns:
        The content of the specified section
    """
    # Pattern to find the section and its content
    pattern = rf'\\section\{{{re.escape(section_name)}\}}(.*?)(?=\\section\{{|\\end\{{document\}})'
    
    # Find the section content
    match = re.search(pattern, latex_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return ""