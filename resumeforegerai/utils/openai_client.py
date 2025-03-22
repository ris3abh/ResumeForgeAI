"""
Utility for initializing and managing OpenAI clients.
"""
import os
from langchain_openai import ChatOpenAI
from openai import OpenAI

def get_openai_api_key():
    """Get the OpenAI API key from environment variables.
    
    Returns:
        The API key
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return api_key.strip()  # Ensure no whitespace

def create_chat_openai(model_name="gpt-4o", temperature=0.2):
    """Create a ChatOpenAI instance with the specified configuration.
    
    Args:
        model_name: Name of the OpenAI model to use
        temperature: Temperature for generation
        
    Returns:
        Configured ChatOpenAI instance
    """
    api_key = get_openai_api_key()
    
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key
    )

def create_openai_client():
    """Create a direct OpenAI client instance.
    
    Returns:
        Configured OpenAI client
    """
    api_key = get_openai_api_key()
    
    return OpenAI(api_key=api_key)

def test_openai_connection():
    """Test the OpenAI connection by making a simple API call.
    
    Returns:
        True if successful, raises an exception otherwise
    """
    client = create_openai_client()
    
    # Make a minimal API call to verify the key works
    try:
        # Just list models without parameters
        models = client.models.list()
        return True
    except Exception as e:
        raise ConnectionError(f"Failed to connect to OpenAI API: {str(e)}")