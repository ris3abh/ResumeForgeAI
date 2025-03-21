import os
import json
from typing import Dict, Any, List, Optional

def read_text_file(file_path: str) -> str:
    """Read text content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The content of the file as a string
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def write_text_file(file_path: str, content: str) -> None:
    """Write text content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read JSON content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The parsed JSON content
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_json_file(file_path: str, content: Dict[str, Any]) -> None:
    """Write JSON content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(content, file, indent=2)

def load_phase_config() -> Dict[str, Any]:
    """Load the phases configuration.
    
    Returns:
        The phases configuration
    """
    return read_json_file('config/phases.json')

def load_agent_config(agent_id: str) -> Dict[str, Any]:
    """Load the configuration for a specific agent.
    
    Args:
        agent_id: ID of the agent to load configuration for
        
    Returns:
        The agent configuration
    """
    return read_json_file(f'config/agents/{agent_id}.json')

def load_all_agent_configs() -> Dict[str, Dict[str, Any]]:
    """Load configurations for all agents.
    
    Returns:
        Dictionary mapping agent IDs to their configurations
    """
    agents = {}
    agent_dir = 'config/agents'
    
    for filename in os.listdir(agent_dir):
        if filename.endswith('.json'):
            agent_id = filename[:-5]  # Remove .json extension
            agents[agent_id] = read_json_file(os.path.join(agent_dir, filename))
    
    return agents