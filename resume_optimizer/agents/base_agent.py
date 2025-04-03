"""Base agent class for optimizer agents."""

from abc import ABC, abstractmethod
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from resume_optimizer.utils.model_factory import create_default_model


class BaseOptimizerAgent(ABC):
    """Base class for all optimizer agents."""
    
    def __init__(self, role_name, system_message_content, model=None):
        """Initialize the agent with a role and system message.
        
        Args:
            role_name: The name/role of the agent
            system_message_content: Content for the system message
            model: Optional model to use, otherwise uses default
        """
        self.role_name = role_name
        self.system_message = BaseMessage.make_assistant_message(
            role_name=role_name,
            content=system_message_content
        )
        self.model = model if model else create_default_model()
        self.agent = ChatAgent(
            system_message=self.system_message,
            model=self.model
        )
    
    def process(self, user_message_content):
        """Process a user message and return the agent's response.
        
        Args:
            user_message_content: Content of the user message
            
        Returns:
            The agent's response message content
        """
        user_message = BaseMessage.make_user_message(
            role_name="User",
            content=user_message_content
        )
        response = self.agent.step(user_message)
        return response.msgs[0].content
    
    @abstractmethod
    def optimize(self, content, context):
        """Optimize content based on context.
        
        Args:
            content: The content to optimize
            context: Contextual information for optimization
            
        Returns:
            Optimized content
        """
        pass