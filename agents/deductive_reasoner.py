"""
Deductive Reasoner - Connects job requirements with resume content.
"""

from camel.agents.deductive_reasoner_agent import DeductiveReasonerAgent as CAMELDeductiveAgent
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from config.prompts import DEDUCTIVE_REASONER_SYSTEM_PROMPT, DEDUCTION_PROMPT

def create_deductive_reasoner_agent(model=None):
    """Create a deductive reasoner agent."""
    if model:
        return CAMELDeductiveAgent(model=model)
    return CAMELDeductiveAgent()

def create_custom_reasoner_agent(model=None):
    """Create a custom deductive reasoner agent using standard ChatAgent."""
    # Create the system message for the agent
    system_msg = BaseMessage.make_assistant_message(
        role_name="Deductive Reasoner",
        content=DEDUCTIVE_REASONER_SYSTEM_PROMPT
    )
    
    # Create and return the agent
    return ChatAgent(system_message=system_msg, model=model)

def deduce_optimization_strategy(job_requirements, resume_structure, agent=None, model=None):
    """
    Use deductive reasoning to develop an optimization strategy.
    
    Args:
        job_requirements (str): The extracted job requirements
        resume_structure (dict): The parsed resume structure
        agent (DeductiveReasonerAgent, optional): An existing agent to use
        model: Model to use if creating a new agent
        
    Returns:
        dict: The optimization strategy with conditions and quality assessment
    """
    # Try using CAMEL's built-in DeductiveReasonerAgent if no agent provided
    if agent is None:
        agent = create_deductive_reasoner_agent(model)
    
    try:
        # Use CAMEL's built-in deduction method
        result = agent.deduce_conditions_and_quality(
            starting_state=str(resume_structure),
            target_state=job_requirements
        )
        return result
    except Exception as e:
        # Fall back to custom implementation if CAMEL's method fails
        print(f"Using custom reasoner due to: {str(e)}")
        custom_agent = create_custom_reasoner_agent(model)
        
        # Prepare the prompt
        prompt = DEDUCTION_PROMPT.format(
            job_requirements=job_requirements,
            resume_structure=str(resume_structure)
        )
        
        # Create the user message
        user_message = BaseMessage.make_user_message(
            role_name="User",
            content=prompt
        )
        
        # Get the agent's response
        response = custom_agent.step(user_message)
        
        # Return a formatted response to match the expected structure
        return {
            "conditions": response.msgs[0].content,
            "quality": "Custom reasoning response"
        }