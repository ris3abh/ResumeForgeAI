"""
Job Analyzer - Extracts key requirements from job descriptions.
"""

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from config.prompts import JOB_ANALYZER_SYSTEM_PROMPT, JOB_ANALYSIS_PROMPT

def create_job_analyzer_agent(model=None):
    """Create a job analyzer agent."""
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Job Analyzer",
        content=JOB_ANALYZER_SYSTEM_PROMPT
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg, model=model)

def analyze_job_description(job_description, agent=None, model=None):
    """
    Analyze a job description to extract key requirements.
    
    Args:
        job_description (str): The job description text
        agent (ChatAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        str: Structured job requirements
    """
    # Create the agent if not provided
    if agent is None:
        agent = create_job_analyzer_agent(model)
    
    # Prepare the prompt
    prompt = JOB_ANALYSIS_PROMPT.format(job_description=job_description)
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    
    # Return the analysis
    return response.msgs[0].content