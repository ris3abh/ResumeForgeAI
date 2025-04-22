"""
Coordinator Agent - Orchestrates the resume customization process.
"""

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from config.prompts import COORDINATOR_SYSTEM_PROMPT, COORDINATION_PROMPT

def create_coordinator_agent(model=None):
    """Create a coordinator agent to orchestrate the resume customization process."""
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Coordinator",
        content=COORDINATOR_SYSTEM_PROMPT
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg, model=model)

def coordinate_optimization(resume_structure, job_requirements, agent=None, model=None):
    """
    Coordinate the optimization strategy across all resume sections.
    
    Args:
        resume_structure (dict): The parsed resume structure
        job_requirements (str): The extracted job requirements
        agent (ChatAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        dict: The coordination plan with priorities and strategies
    """
    # Create the agent if not provided
    if agent is None:
        agent = create_coordinator_agent(model)
    
    # Prepare the prompt
    prompt = COORDINATION_PROMPT.format(
        resume_structure=str(resume_structure),
        job_requirements=job_requirements
    )
    
    # Create the user message
    user_message = BaseMessage.make_user_message(
        role_name="User",
        content=prompt
    )
    
    # Get the agent's response
    response = agent.step(user_message)
    coordination_plan = response.msgs[0].content
    
    # Parse the priorities from the plan
    section_priorities = parse_section_priorities(coordination_plan)
    
    return {
        "plan": coordination_plan,
        "priorities": section_priorities
    }

def parse_section_priorities(coordination_plan):
    """Extract the section priorities from the coordination plan."""
    # This is a simplified parsing approach - in production, you'd want more robust parsing
    section_types = [
        "summary", "experience", "skills", "education", 
        "projects", "certifications", "publications"
    ]
    
    priorities = {}
    for section in section_types:
        # Check if section is mentioned in the plan
        if section.lower() in coordination_plan.lower():
            # Rough priority estimation based on position in the text
            position = coordination_plan.lower().find(section.lower())
            priorities[section] = position
    
    # Sort sections by position (earlier = higher priority)
    sorted_sections = sorted(priorities.keys(), key=lambda x: priorities[x])
    
    # Assign numeric priorities
    return {section: i+1 for i, section in enumerate(sorted_sections)}