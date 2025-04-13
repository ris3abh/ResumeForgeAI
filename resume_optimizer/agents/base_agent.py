"""Base agent class for optimizer agents with enhanced memory capabilities."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.types import OpenAIBackendRole
from camel.memories import (
    ChatHistoryMemory, 
    LongtermAgentMemory,
    ChatHistoryBlock,
    VectorDBBlock,
    ScoreBasedContextCreator,
    MemoryRecord
)
from camel.utils import OpenAITokenCounter
from camel.types import ModelType

from resume_optimizer.utils.model_factory import create_default_model, create_fallback_model

logger = logging.getLogger(__name__)

class BaseOptimizerAgent(ABC):
    """Base class for all optimizer agents with enhanced memory capabilities."""
    
    def __init__(
        self, 
        role_name: str, 
        system_message_content: str, 
        model=None,
        use_memory: bool = True,
        memory_token_limit: int = 4096,
        retry_on_failure: bool = True
    ):
        """Initialize the agent with a role and system message.
        
        Args:
            role_name: The name/role of the agent
            system_message_content: Content for the system message
            model: Optional model to use, otherwise uses default
            use_memory: Whether to use memory capabilities
            memory_token_limit: Token limit for memory context
            retry_on_failure: Whether to retry with fallback model on failure
        """
        self.role_name = role_name
        self.system_message = BaseMessage.make_assistant_message(
            role_name=role_name,
            content=system_message_content
        )
        self.model = model if model else create_default_model()
        self.retry_on_failure = retry_on_failure
        self.use_memory = use_memory
        
        # Initialize ChatAgent with memory
        if self.use_memory:
            # Create token counter for context creation
            token_counter = OpenAITokenCounter(ModelType.GPT_4O_MINI)
            
            # Create context creator with token limit
            context_creator = ScoreBasedContextCreator(
                token_counter=token_counter,
                token_limit=memory_token_limit
            )
            
            # Initialize memory components
            self.memory = LongtermAgentMemory(
                context_creator=context_creator,
                chat_history_block=ChatHistoryBlock(),
                vector_db_block=VectorDBBlock()
            )
            
            self.agent = ChatAgent(
                system_message=self.system_message,
                model=self.model,
                memory=self.memory
            )
        else:
            self.memory = None
            self.agent = ChatAgent(
                system_message=self.system_message,
                model=self.model
            )
    
    def process(self, user_message_content: str) -> str:
        """Process a user message and return the agent's response with error handling.
        
        Args:
            user_message_content: Content of the user message
            
        Returns:
            The agent's response message content
        """
        user_message = BaseMessage.make_user_message(
            role_name="User",
            content=user_message_content
        )
        
        try:
            # Try with primary model
            response = self.agent.step(user_message)
            return response.msgs[0].content
        except Exception as e:
            logger.error(f"Error processing with primary model: {str(e)}")
            
            if self.retry_on_failure:
                logger.info("Retrying with fallback model")
                try:
                    # Create temporary agent with fallback model
                    fallback_model = create_fallback_model()
                    fallback_agent = ChatAgent(
                        system_message=self.system_message,
                        model=fallback_model
                    )
                    fallback_response = fallback_agent.step(user_message)
                    return fallback_response.msgs[0].content
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {str(fallback_error)}")
                    raise RuntimeError(f"Failed to process message: {str(e)}. Fallback also failed: {str(fallback_error)}")
            else:
                raise RuntimeError(f"Failed to process message: {str(e)}")
    
    def save_to_memory(self, content: str, role: str = "assistant") -> None:
        """Save content to the agent's memory.
        
        Args:
            content: Content to save
            role: Role for the memory record (assistant or user)
        """
        if not self.memory:
            logger.warning("Memory not enabled for this agent")
            return
            
        # Create a message
        if role.lower() == "user":
            message = BaseMessage.make_user_message(
                role_name="User",
                content=content
            )
            backend_role = OpenAIBackendRole.USER
        else:
            message = BaseMessage.make_assistant_message(
                role_name=self.role_name,
                content=content
            )
            backend_role = OpenAIBackendRole.ASSISTANT
            
        # Create and save memory record
        record = MemoryRecord(message=message, role_at_backend=backend_role)
        self.memory.write_record(record)
    
    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        if self.memory:
            self.memory.clear()
            logger.info(f"Memory cleared for agent: {self.role_name}")
        else:
            logger.warning("Memory not enabled for this agent")
    
    @abstractmethod
    def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Optimize content based on context.
        
        Args:
            content: The content to optimize
            context: Contextual information for optimization
            
        Returns:
            Optimized content
        """
        pass