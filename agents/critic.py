"""
Critic Agent - Evaluates optimized resumes and provides feedback.
"""

from camel.agents import CriticAgent
from camel.messages import BaseMessage
from config.prompts import CRITIC_SYSTEM_PROMPT, CRITIQUE_PROMPT

def create_critic_agent(model=None):
    """Create a critic agent to evaluate the optimized resume."""
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Resume Critic",
        content=CRITIC_SYSTEM_PROMPT
    )
    
    # Create and return the agent
    return CriticAgent(system_message=system_msg, model=model)

def critique_resume(original_resume, optimized_resume, job_requirements, agent=None, model=None):
    """
    Critique the optimized resume against job requirements.
    
    Args:
        original_resume (str): The original LaTeX resume content
        optimized_resume (str): The optimized LaTeX resume content
        job_requirements (str): The extracted job requirements
        agent (CriticAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        str: Critique feedback
    """
    # Create the agent if not provided
    if agent is None:
        agent = create_critic_agent(model)
    
    # Prepare the prompt
    prompt = CRITIQUE_PROMPT.format(
        job_requirements=job_requirements,
        original_resume=original_resume[:1000] + "..." if len(original_resume) > 1000 else original_resume,
        optimized_resume=optimized_resume[:1000] + "..." if len(optimized_resume) > 1000 else optimized_resume
    )
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    
    return response.msgs[0].content

def extract_rating(critique):
    """Extract the numerical rating from the critique."""
    import re
    
    # Look for a rating pattern like "Rating: 7/10" or "I give this a 7 out of 10"
    rating_patterns = [
        r'rating:\s*(\d+)(?:\s*\/\s*10)',
        r'(\d+)(?:\s*\/\s*10)',
        r'score of (\d+)',
        r'rate.*?(\d+)'
    ]
    
    for pattern in rating_patterns:
        match = re.search(pattern, critique.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
    
    return None  # If no rating found