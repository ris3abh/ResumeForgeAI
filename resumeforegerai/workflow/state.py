from typing import Dict, List, Optional, Any, TypedDict
from typing_extensions import Annotated
from langchain_core.messages import BaseMessage

# Define reducer functions for different types

def combine_messages(x: List[BaseMessage], y: List[BaseMessage]) -> List[BaseMessage]:
    """Combine two lists of messages."""
    return x + y

def combine_phases(x: List[str], y: List[str]) -> List[str]:
    """Combine two lists of completed phases."""
    return x + y

def last_value(x: Any, y: Any) -> Any:
    """Just keep the last value."""
    return y

class GraphState(TypedDict):
    """State definition for the resume automation workflow."""
    
    # Messages exchanged between agents
    messages: Annotated[List[BaseMessage], combine_messages]
    
    # Phase tracking
    current_phase: Annotated[str, last_value]
    completed_phases: Annotated[List[str], combine_phases]
    
    # Input files
    resume_file: Annotated[Optional[str], last_value]
    job_description_file: Annotated[Optional[str], last_value]
    
    # Analysis results
    resume_analysis: Annotated[Optional[Dict[str, Any]], last_value]
    job_analysis: Annotated[Optional[Dict[str, Any]], last_value]
    
    # Orchestration
    task_plan: Annotated[Optional[Dict[str, Any]], last_value]
    agent_assignments: Annotated[Optional[Dict[str, Any]], last_value]
    
    # Work Experience Customization
    work_experience_customization: Annotated[Optional[Dict[str, Any]], last_value]
    work_experience_validation: Annotated[Optional[Dict[str, Any]], last_value]
    
    # Skills Customization
    skills_customization: Annotated[Optional[Dict[str, Any]], last_value]
    skills_validation: Annotated[Optional[Dict[str, Any]], last_value]
    
    # Compliance
    compliance_verification: Annotated[Optional[Dict[str, Any]], last_value]
    
    # Output
    tailored_resume: Annotated[Optional[str], last_value]
    
    # Control flow
    next: Annotated[str, last_value]
    error: Annotated[Optional[str], last_value]