"""
Job Analyzer - Extracts key requirements from job descriptions.
"""

from camel.agents import ChatAgent
from camel.messages import BaseMessage


def create_job_analyzer_agent():
    """Create a job analyzer agent."""
    system_message = """
    You are a job description analyzer. Your task is to:
    1. Extract hard skills (technical requirements) from job descriptions
    2. Identify soft skills mentioned or implied in the job posting
    3. Recognize industry-specific keywords and terminology
    4. Categorize requirements by importance (required vs. preferred)
    5. Create a structured list of keywords and phrases to include in the resume
    """
    
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Job Analyzer",
        content=system_message
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg)


def analyze_job_description(job_description):
    """
    Analyze a job description to extract key requirements.
    
    Args:
        job_description (str): The job description text
        
    Returns:
        dict: Structured job requirements
    """
    # Create the agent
    agent = create_job_analyzer_agent()
    
    # Prepare the prompt
    prompt = f"""
    Please analyze the following job description to extract key requirements.
    Provide your response in a structured format with these categories:
    1. Hard Skills (technical requirements)
    2. Soft Skills
    3. Experience Requirements
    4. Education Requirements
    5. Industry-Specific Keywords
    6. Must-Have vs. Nice-to-Have
    
    Job Description:
    {job_description}
    """
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    
    # Return the analysis
    return response.msgs[0].content