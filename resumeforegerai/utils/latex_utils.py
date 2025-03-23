import re
from typing import Dict, List, Optional, Any

def extract_latex_sections(latex_content: str) -> Dict[str, str]:
    """Extract sections from a LaTeX document.
    
    Args:
        latex_content: The content of the LaTeX file
        
    Returns:
        Dictionary mapping section names to their content
    """
    sections = {}
    
    # Find section commands
    section_pattern = r'\\section\{([^}]+)\}(.*?)(?=\\section\{|\\end\{document\})'
    subsection_pattern = r'\\subsection\{([^}]+)\}(.*?)(?=\\subsection\{|\\section\{|\\end\{document\})'
    
    # Extract main sections with their content
    for match in re.finditer(section_pattern, latex_content, re.DOTALL):
        section_name = match.group(1)
        section_content = match.group(2).strip()
        sections[section_name] = section_content
    
    return sections

def extract_latex_commands(latex_content: str) -> List[str]:
    """Extract custom commands from a LaTeX document.
    
    Args:
        latex_content: The content of the LaTeX file
        
    Returns:
        List of custom command definitions
    """
    commands = []
    
    # Find newcommand definitions
    command_pattern = r'\\newcommand\{([^}]+)\}(\[[^\]]+\])?\{([^}]+)\}'
    
    for match in re.finditer(command_pattern, latex_content):
        command_name = match.group(1)
        command_args = match.group(2) if match.group(2) else ""
        command_def = match.group(3)
        
        commands.append(f"\\newcommand{{{command_name}}}{command_args}{{{command_def}}}")
    
    return commands

def extract_latex_packages(latex_content: str) -> List[Dict[str, str]]:
    """Extract package imports from a LaTeX document.
    
    Args:
        latex_content: The content of the LaTeX file
        
    Returns:
        List of package information (name and options)
    """
    packages = []
    
    # Find usepackage commands
    package_pattern = r'\\usepackage(\[[^]]+\])?\{([^}]+)\}'
    
    for match in re.finditer(package_pattern, latex_content):
        options = match.group(1) if match.group(1) else ""
        package_name = match.group(2)
        
        packages.append({
            "name": package_name,
            "options": options.strip('[]') if options else ""
        })
    
    return packages

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

def analyze_latex_structure(latex_content: str) -> Dict[str, Any]:
    """Analyze the structure of a LaTeX document.
    
    Args:
        latex_content: The content of the LaTeX file
        
    Returns:
        Dictionary with analysis results
    """
    result = {
        "document_class": None,
        "packages": extract_latex_packages(latex_content),
        "commands": extract_latex_commands(latex_content),
        "sections": extract_latex_sections(latex_content),
        "environments": []
    }
    
    # Extract document class
    doc_class_match = re.search(r'\\documentclass(\[[^]]+\])?\{([^}]+)\}', latex_content)
    if doc_class_match:
        options = doc_class_match.group(1) if doc_class_match.group(1) else ""
        class_name = doc_class_match.group(2)
        
        result["document_class"] = {
            "name": class_name,
            "options": options.strip('[]') if options else ""
        }
    
    # Extract environments
    env_pattern = r'\\begin\{([^}]+)\}(.*?)\\end\{\1\}'
    for match in re.finditer(env_pattern, latex_content, re.DOTALL):
        env_name = match.group(1)
        env_content = match.group(2).strip()
        
        result["environments"].append({
            "name": env_name,
            "content": env_content if len(env_content) < 100 else env_content[:100] + "..."
        })
    
    return result