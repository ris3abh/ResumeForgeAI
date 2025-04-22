"""
Resume Parser - Identifies sections in a LaTeX resume.
"""

import re
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from config.prompts import RESUME_PARSER_SYSTEM_PROMPT, RESUME_PARSING_PROMPT

def create_resume_parser_agent(model=None):
    """Create a resume parser agent."""
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Resume Parser",
        content=RESUME_PARSER_SYSTEM_PROMPT
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg, model=model)

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
        dict: The section info with name, content, start and end positions
    """
    start, end = identify_section_boundaries(latex_content, section_name)
    if start is not None and end is not None:
        return {
            "name": section_name,
            "content": latex_content[start:end],
            "start": start,
            "end": end
        }
    return None

def parse_resume(latex_content, agent=None, model=None):
    """
    Parse a LaTeX resume to identify its structure and key sections.
    
    Args:
        latex_content (str): The LaTeX resume content
        agent (ChatAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        dict: The parsed resume structure
    """
    # Create the agent if not provided
    if agent is None:
        agent = create_resume_parser_agent(model)
    
    # Prepare the prompt
    prompt = RESUME_PARSING_PROMPT.format(resume_content=latex_content)
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    agent_analysis = response.msgs[0].content
    
    # Now let's do our own parsing to get exact section boundaries
    common_section_names = {
        "summary": ["summary", "professional summary", "profile", "about me"],
        "experience": ["experience", "work experience", "professional experience", "employment history", "work history"],
        "skills": ["skills", "technical skills", "competencies", "core competencies", "expertise"],
        "education": ["education", "academic background", "academic history", "qualifications"],
        "projects": ["projects", "project experience", "relevant projects"],
        "certifications": ["certifications", "certificates", "professional certifications"],
        "publications": ["publications", "research", "papers"],
        "awards": ["awards", "honors", "achievements", "recognitions"]
    }
    
    # Parse all sections
    sections = {}
    for section_type, section_names in common_section_names.items():
        for name in section_names:
            section = extract_section_content(latex_content, name)
            if section:
                sections[section_type] = section
                break
    
    return {
        "agent_analysis": agent_analysis,
        "sections": sections
    }