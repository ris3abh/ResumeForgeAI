"""Model factory for creating and managing AI models with robust error handling."""

import os
import logging
from typing import Optional, Dict, Any, Union

from camel.models import ModelFactory as CamelModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

logger = logging.getLogger(__name__)

def create_default_model(model_type: Optional[ModelType] = None):
    """Create a default model for agents to use with improved error handling.
    
    Args:
        model_type: Optional specific model type to use, defaults to GPT_4O_MINI
        
    Returns:
        A configured model instance ready for use with agents.
        
    Raises:
        RuntimeError: If model creation fails due to missing API keys or configuration issues
    """
    try:
        # Use specified model type or default to GPT_4O_MINI
        model_type = model_type or ModelType.GPT_4O_MINI
        
        # Create model config with reasonable defaults
        # Only use parameters that are valid for the ChatGPTConfig
        model_config = ChatGPTConfig(
            temperature=0.7,
            top_p=0.95,
        ).as_dict()
        
        # Check for API key
        if "OPENAI_API_KEY" not in os.environ:
            logger.warning("OPENAI_API_KEY not found in environment, model might fail")
        
        logger.info(f"Creating model: {model_type}")
        return CamelModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=model_type,
            model_config_dict=model_config,
        )
        
    except Exception as e:
        logger.error(f"Failed to create model: {str(e)}")
        raise RuntimeError(f"Model creation failed: {str(e)}")

def create_fallback_model():
    """Create a fallback model in case the primary model fails.
    
    This uses a more reliable but potentially less capable model.
    
    Returns:
        A configured model instance
    """
    try:
        logger.info("Creating fallback model")
        model_config = ChatGPTConfig(
            temperature=0.5,  # Lower temperature for more deterministic outputs
            max_tokens=2048,  # Limit token usage
        ).as_dict()
        
        return CamelModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_3_5_TURBO,  # More reliable fallback
            model_config_dict=model_config,
        )
    except Exception as e:
        logger.error(f"Failed to create fallback model: {str(e)}")
        raise RuntimeError(f"Fallback model creation failed: {str(e)}")

def get_model_by_name(model_name: str):
    """Get a model by name string.
    
    Args:
        model_name: String representation of model name
        
    Returns:
        Configured model instance
        
    Raises:
        ValueError: If model name is not recognized
    """
    model_name = model_name.upper() if model_name else None
    
    if model_name == "GPT4O" or model_name == "GPT-4O":
        return create_default_model(ModelType.GPT_4O)
    elif model_name == "GPT4" or model_name == "GPT-4":
        return create_default_model(ModelType.GPT_4)
    elif model_name == "GPT35TURBO" or model_name == "GPT-3.5-TURBO":
        return create_default_model(ModelType.GPT_3_5_TURBO)
    elif model_name == "GPT4OMINI" or model_name == "GPT-4O-MINI" or not model_name:
        return create_default_model(ModelType.GPT_4O_MINI)
    else:
        try:
            model_type = getattr(ModelType, model_name)
            return create_default_model(model_type)
        except (AttributeError, TypeError):
            logger.error(f"Unknown model name: {model_name}, using default")
            return create_default_model()