"""
Resume Optimizer - Optimizes a resume based on job requirements.
"""

from camel.agents import ChatAgent
from camel.messages import BaseMessage


def create_optimizer_agent():
    """Create a resume optimizer agent."""
    system_message = """
    You are a resume optimization expert. Your job is to:
    1. Analyze job requirements and resume content
    2. Enhance resume sections to better match job requirements
    3. Incorporate relevant keywords naturally into the resume
    4. Ensure the LaTeX syntax remains intact and valid
    5. Focus specifically on optimizing the work experience and skills sections
    """
    
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Resume Optimizer",
        content=system_message
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg)


def optimize_section(agent, section_content, job_requirements, section_type):
    """
    Optimize a section of the resume.
    
    Args:
        agent (ChatAgent): The optimizer agent
        section_content (str): The content of the section to optimize
        job_requirements (str): The extracted job requirements
        section_type (str): The type of section being optimized ("experience" or "skills")
        
    Returns:
        str: The optimized section content
    """
    # Prepare the prompt
    prompt = f"""
    Please optimize the following {section_type} section from a LaTeX resume to better match the job requirements.
    
    Job Requirements:
    {job_requirements}
    
    {section_type.capitalize()} Section:
    {section_content}
    
    Guidelines:
    1. Enhance descriptions to emphasize relevant skills that match the job requirements
    2. Incorporate job-specific keywords naturally
    3. Maintain the exact same LaTeX structure and formatting
    4. Do not add fictional experience or skills
    5. Return ONLY the optimized LaTeX code, with no explanations, comments, or markdown formatting
    6. Do not include ```latex or ``` markers
    7. Your response should begin with the LaTeX command that starts the section
    8. Your response should be a direct drop-in replacement for the original section
    """
    
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
        import re
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


def optimize_resume(latex_content, resume_structure, job_requirements):
    """
    Optimize a resume based on job requirements.
    
    Args:
        latex_content (str): The original LaTeX resume content
        resume_structure (dict): The parsed resume structure
        job_requirements (str): The extracted job requirements
        
    Returns:
        str: The optimized LaTeX resume content
    """
    # Create the optimizer agent
    agent = create_optimizer_agent()
    
    # Optimize the experience section if found
    optimized_latex = latex_content
    if resume_structure["experience_section"]:
        experience = resume_structure["experience_section"]
        optimized_experience = optimize_section(
            agent, 
            experience["content"], 
            job_requirements, 
            "experience"
        )
        
        # Replace the experience section in the document
        optimized_latex = (
            optimized_latex[:experience["start"]] +
            optimized_experience +
            optimized_latex[experience["end"]:]
        )
    
    # Optimize the skills section if found
    if resume_structure["skills_section"]:
        # Need to update the structure since the document has changed if experience was modified
        if resume_structure["experience_section"]:
            # Recalculate skills section position if experience was modified
            from agents.resume_parser import identify_section_boundaries
            skills_name = resume_structure["skills_section"]["name"]
            start, end = identify_section_boundaries(optimized_latex, skills_name)
            skills = {
                "name": skills_name,
                "content": optimized_latex[start:end],
                "start": start,
                "end": end
            }
        else:
            skills = resume_structure["skills_section"]
        
        optimized_skills = optimize_section(
            agent, 
            skills["content"], 
            job_requirements, 
            "skills"
        )
        
        # Replace the skills section in the document
        optimized_latex = (
            optimized_latex[:skills["start"]] +
            optimized_skills +
            optimized_latex[skills["end"]:]
        )
    
    return optimized_latex