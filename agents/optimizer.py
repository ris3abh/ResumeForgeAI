"""
Resume Optimizer - Optimizes a resume based on job requirements.
"""

import re
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from config.prompts import RESUME_OPTIMIZER_SYSTEM_PROMPT, SECTION_OPTIMIZATION_PROMPT, ACTION_VERBS

def create_optimizer_agent(model=None):
    """Create a resume optimizer agent."""
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Resume Optimizer",
        content=RESUME_OPTIMIZER_SYSTEM_PROMPT
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg, model=model)

def optimize_section(section_content, section_name, job_requirements, 
                    optimization_strategy=None, agent=None, model=None):
    """
    Optimize a section of the resume.
    
    Args:
        section_content (str): The content of the section to optimize
        section_name (str): The type of section being optimized
        job_requirements (str): The extracted job requirements
        optimization_strategy (str, optional): Strategy from the deductive reasoner
        agent (ChatAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        str: The optimized section content
    """
    # Create the agent if not provided
    if agent is None:
        agent = create_optimizer_agent(model)
    
    # Prepare the prompt
    prompt = SECTION_OPTIMIZATION_PROMPT.format(
        section_name=section_name,
        job_requirements=job_requirements,
        section_content=section_content
    )
    
    # Add optimization strategy if provided
    if optimization_strategy:
        prompt += f"\n\nOptimization Strategy:\n{optimization_strategy}"
    
    # Remind about action verbs for certain sections
    if section_name.lower() in ["experience", "work experience", "professional experience"]:
        prompt += "\n\nRemember to use strong action verbs from this list to start bullet points: " + \
                 ", ".join(ACTION_VERBS[:10]) + "... and others. " + \
                 "Make bullet points 17-19 words long and include metrics where possible."
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    optimized_content = response.msgs[0].content
    
    # Clean up the response to remove any markdown formatting or explanations
    if '```' in optimized_content:
        # Extract only the LaTeX code from a code block if present
        latex_code = re.search(r'```(?:latex)?(.*?)```', optimized_content, re.DOTALL)
        if latex_code:
            optimized_content = latex_code.group(1).strip()
    
    # Ensure the section starts with the appropriate LaTeX command
    if not optimized_content.strip().startswith('\\section'):
        # If the section command is missing, prepend it
        section_cmd = re.search(r'(\\section\{[^}]+\})', section_content)
        if section_cmd:
            optimized_content = section_cmd.group(1) + '\n' + optimized_content
    
    return optimized_content

def optimize_resume(latex_content, resume_structure, job_requirements, 
                   optimization_strategy=None, sections_to_optimize=None,
                   agent=None, model=None):
    """
    Optimize a resume based on job requirements.
    
    Args:
        latex_content (str): The original LaTeX resume content
        resume_structure (dict): The parsed resume structure
        job_requirements (str): The extracted job requirements
        optimization_strategy (str, optional): Strategy from the deductive reasoner
        sections_to_optimize (list, optional): Specific sections to optimize
        agent (ChatAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        str: The optimized LaTeX resume content
    """
    # Create the optimizer agent
    if agent is None:
        agent = create_optimizer_agent(model)
    
    # Start with the original content
    optimized_latex = latex_content
    
    # Get the sections from the resume structure
    sections = resume_structure.get("sections", {})
    
    # If specific sections were provided, only optimize those
    if sections_to_optimize:
        sections_to_process = {k: v for k, v in sections.items() if k in sections_to_optimize}
    else:
        sections_to_process = sections
    
    # Optimize each section
    for section_type, section_info in sections_to_process.items():
        # Skip if section info is missing
        if not section_info:
            continue
        
        optimized_section = optimize_section(
            section_info["content"], 
            section_info["name"], 
            job_requirements,
            optimization_strategy,
            agent,
            model
        )
        
        # Replace the section in the document
        optimized_latex = (
            optimized_latex[:section_info["start"]] +
            optimized_section +
            optimized_latex[section_info["end"]:]
        )
        
        # Update the positions of subsequent sections
        offset = len(optimized_section) - (section_info["end"] - section_info["start"])
        for other_type, other_info in sections.items():
            if other_info and other_info["start"] > section_info["start"]:
                other_info["start"] += offset
                other_info["end"] += offset
    
    return optimized_latex