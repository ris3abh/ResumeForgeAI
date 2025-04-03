"""Model factory for creating and managing AI models."""

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

def create_default_model():
    """Create a default model for agents to use.
    
    Returns:
        A configured model instance ready for use with agents.
    """
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
        model_config_dict=ChatGPTConfig().as_dict(),
    )