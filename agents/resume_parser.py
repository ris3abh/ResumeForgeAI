"""
Resume Parser - Identifies sections in a LaTeX resume.
"""

import re
from camel.agents import ChatAgent
from camel.messages import BaseMessage


def create_resume_parser_agent():
    """Create a resume parser agent."""
    system_message = """
    You are a LaTeX resume parser. Your job is to:
    1. Identify the structure of LaTeX resumes without modifying them
    2. Locate the work experience and skills sections precisely
    3. Extract the content within these sections for analysis
    4. Document the exact LaTeX commands and structure used
    5. Create a map of the document that will allow for precise modifications later
    """
    
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Resume Parser",
        content=system_message
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg)


def identify_section_boundaries(latex_content, section_name):
    """
    Find the start and end positions of a section in the LaTeX content.
    
    Args:
        latex_content (str): The LaTeX resume content
        section_name (str): The name of the section to find
        
    Returns:
        tuple: (start_pos, end_pos) of the section, or (None, None) if not found
    """
    # Try different patterns for section declarations
    patterns = [
        rf'\\section\{{\s*{section_name}\s*\}}',
        rf'\\section\*\{{\s*{section_name}\s*\}}',
        rf'\\resumesection\{{\s*{section_name}\s*\}}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, latex_content, re.IGNORECASE)
        if match:
            section_start = match.start()
            
            # Find the next section or the end of the document
            next_section = re.search(r'\\section', latex_content[section_start + len(match.group(0)):])
            if next_section:
                section_end = section_start + len(match.group(0)) + next_section.start()
            else:
                section_end = len(latex_content)
                
            return section_start, section_end
    
    return None, None


def extract_section_content(latex_content, section_name):
    """
    Extract the content of a section from the LaTeX resume.
    
    Args:
        latex_content (str): The LaTeX resume content
        section_name (str): The name of the section to extract
        
    Returns:
        str: The content of the section, or an empty string if not found
    """
    start, end = identify_section_boundaries(latex_content, section_name)
    if start is not None and end is not None:
        return latex_content[start:end]
    return ""


def parse_resume(latex_content):
    """
    Parse a LaTeX resume to identify its structure and key sections.
    
    Args:
        latex_content (str): The LaTeX resume content
        
    Returns:
        dict: The parsed resume structure
    """
    # Create the agent
    agent = create_resume_parser_agent()
    
    # Prepare the prompt
    prompt = f"""
    Please analyze the following LaTeX resume to identify its structure.
    Focus especially on locating the "experience" and "skills" sections.
    
    LaTeX Resume:
    {latex_content[:3000]}  # Limiting to first 3000 chars for this prompt
    
    For each identified section, provide:
    1. The section name
    2. The LaTeX command used to define the section
    3. Any key environments or formatting used within the section
    
    Please be precise about the experience and skills sections, as we'll need to modify them later.
    """
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    agent_analysis = response.msgs[0].content
    
    # Now let's do our own parsing to get exact section boundaries
    experience_section_names = ["experience", "work experience", "professional experience", 
                               "employment history", "work history"]
    skills_section_names = ["skills", "technical skills", "competencies", 
                           "core competencies", "expertise"]
    
    # Find experience section
    experience_section = None
    for name in experience_section_names:
        content = extract_section_content(latex_content, name)
        if content:
            start, end = identify_section_boundaries(latex_content, name)
            experience_section = {
                "name": name,
                "content": content,
                "start": start,
                "end": end
            }
            break
    
    # Find skills section
    skills_section = None
    for name in skills_section_names:
        content = extract_section_content(latex_content, name)
        if content:
            start, end = identify_section_boundaries(latex_content, name)
            skills_section = {
                "name": name,
                "content": content,
                "start": start,
                "end": end
            }
            break
    
    return {
        "agent_analysis": agent_analysis,
        "experience_section": experience_section,
        "skills_section": skills_section
    }