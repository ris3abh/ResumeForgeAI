from typing import Dict, List, Optional, Any, Sequence, TypedDict, Annotated
from langchain_core.messages import BaseMessage

class GraphState(TypedDict):
    """State definition for the resume automation workflow."""
    
    # Messages exchanged between agents
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation so far"]
    
    # Phase tracking
    current_phase: str
    completed_phases: List[str]
    
    # Input files
    resume_file: Optional[str]
    job_description_file: Optional[str]
    
    # Analysis results
    resume_analysis: Optional[Dict[str, Any]]
    job_analysis: Optional[Dict[str, Any]]
    
    # Orchestration
    task_plan: Optional[Dict[str, Any]]
    agent_assignments: Optional[Dict[str, Any]]
    
    # Work Experience Customization
    work_experience_customization: Optional[Dict[str, Any]]
    work_experience_validation: Optional[Dict[str, Any]]
    
    # Skills Customization
    skills_customization: Optional[Dict[str, Any]]
    skills_validation: Optional[Dict[str, Any]]
    
    # Compliance
    compliance_verification: Optional[Dict[str, Any]]
    
    # Output
    tailored_resume: Optional[str]
    
    # Control flow
    next: str
    error: Optional[str]