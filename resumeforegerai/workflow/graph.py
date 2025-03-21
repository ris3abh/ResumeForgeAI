from typing import Dict, Any, List, Optional
import json

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from workflow.state import GraphState
from utils.file_utils import load_phase_config, read_json_file, write_json_file
from agents.resume_analyzer import ResumeAnalyzerAgent
from agents.job_analyzer import JobAnalyzerAgent


class ResumeAutomationWorkflow:
    """LangGraph workflow for resume automation."""
    
    def __init__(self):
        """Initialize the workflow."""
        # Load configuration
        self.phases_config = load_phase_config()
        
        # Initialize agents
        self.resume_analyzer = ResumeAnalyzerAgent()
        self.job_analyzer = JobAnalyzerAgent()
        
        # Build the workflow graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph.
        
        Returns:
            The configured graph
        """
        # Create the graph
        workflow = StateGraph(GraphState)
        
        # Add nodes for each phase
        for phase in self.phases_config["phases"]:
            # Skip disabled phases
            if phase.get("enabled") is False:
                continue
                
            # Add the phase node
            phase_id = phase["id"]
            
            if phase_id == "resume_analysis":
                workflow.add_node(phase_id, self._run_resume_analysis)
            elif phase_id == "job_description_analysis":
                workflow.add_node(phase_id, self._run_job_analysis)
            elif phase_id == "resume_generation":
                workflow.add_node(phase_id, self._run_resume_generation)
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "resume_analysis",
            self._route_after_resume_analysis,
            {
                "job_description_analysis": "job_description_analysis",
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "job_description_analysis", 
            self._route_after_job_analysis,
            {
                "resume_generation": "resume_generation",
                "end": END,
                "error": END
            }
        )
        
        if "resume_generation" in [p["id"] for p in self.phases_config["phases"] if p.get("enabled") is not False]:
            workflow.add_edge("resume_generation", END)
        
        # Set the entry point
        workflow.set_entry_point("resume_analysis")
        
        return workflow
    
    def _run_resume_analysis(self, state: GraphState) -> GraphState:
        """Run resume analysis phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get the resume file path
            resume_file = state["resume_file"]
            
            # Run the analysis
            analysis_result = self.resume_analyzer.analyze(resume_file)
            
            # Update messages
            messages = list(state["messages"])
            analysis_summary = f"Resume analysis complete. Identified {len(analysis_result.get('sections', []))} sections."
            messages.append(AIMessage(content=analysis_summary, name="ResumeAnalyzer"))
            
            # Update the state
            return {
                **state,
                "messages": messages,
                "resume_analysis": analysis_result,
                "current_phase": "resume_analysis",
                "completed_phases": state["completed_phases"] + ["resume_analysis"],
                "next": "job_description_analysis",
                "error": None
            }
        except Exception as e:
            # Handle errors
            messages = list(state["messages"])
            messages.append(AIMessage(content=f"Error in resume analysis: {str(e)}", name="ResumeAnalyzer"))
            
            return {
                **state,
                "messages": messages,
                "current_phase": "resume_analysis",
                "error": f"Error in resume analysis: {str(e)}",
                "next": "error"
            }
    
    def _run_job_analysis(self, state: GraphState) -> GraphState:
        """Run job description analysis phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get the job description file path and resume analysis
            job_description_file = state["job_description_file"]
            resume_analysis = state["resume_analysis"]
            
            # Run the analysis
            analysis_result = self.job_analyzer.analyze(job_description_file, resume_analysis)
            
            # Update messages
            messages = list(state["messages"])
            analysis_summary = f"Job description analysis complete. Found {len(analysis_result.get('structured_recommendations', {}).get('key_requirements', []))} key requirements."
            messages.append(AIMessage(content=analysis_summary, name="JobAnalyzer"))
            
            # Check if we should proceed to resume generation
            next_phase = "end"
            for phase in self.phases_config["phases"]:
                if phase["id"] == "resume_generation" and phase.get("enabled") is not False:
                    next_phase = "resume_generation"
            
            # Update the state
            return {
                **state,
                "messages": messages,
                "job_analysis": analysis_result,
                "current_phase": "job_description_analysis",
                "completed_phases": state["completed_phases"] + ["job_description_analysis"],
                "next": next_phase,
                "error": None
            }
        except Exception as e:
            # Handle errors
            messages = list(state["messages"])
            messages.append(AIMessage(content=f"Error in job description analysis: {str(e)}", name="JobAnalyzer"))
            
            return {
                **state,
                "messages": messages,
                "current_phase": "job_description_analysis",
                "error": f"Error in job description analysis: {str(e)}",
                "next": "error"
            }
    
    def _run_resume_generation(self, state: GraphState) -> GraphState:
        """Run resume generation phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        # Placeholder for future implementation
        messages = list(state["messages"])
        messages.append(AIMessage(content="Resume generation phase is not implemented yet.", name="ResumeGenerator"))
        
        return {
            **state,
            "messages": messages,
            "current_phase": "resume_generation",
            "completed_phases": state["completed_phases"] + ["resume_generation"],
            "next": END
        }
    
    def _route_after_resume_analysis(self, state: GraphState) -> str:
        """Determine the next phase after resume analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next phase ID
        """
        if state.get("error"):
            return "error"
        return "job_description_analysis"
    
    def _route_after_job_analysis(self, state: GraphState) -> str:
        """Determine the next phase after job analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next phase ID
        """
        if state.get("error"):
            return "error"
        
        # Check if resume generation is enabled
        for phase in self.phases_config["phases"]:
            if phase["id"] == "resume_generation" and phase.get("enabled") is not False:
                return "resume_generation"
        
        return "end"
    
    def run(self, resume_file: str, job_description_file: str) -> Dict[str, Any]:
        """Run the workflow.
        
        Args:
            resume_file: Path to the LaTeX resume file
            job_description_file: Path to the job description file
            
        Returns:
            Results of the workflow
        """
        # Initialize the state
        initial_state = {
            "messages": [],
            "current_phase": "",
            "completed_phases": [],
            "resume_file": resume_file,
            "job_description_file": job_description_file,
            "resume_analysis": None,
            "job_analysis": None,
            "tailored_resume": None,
            "next": "",
            "error": None
        }
        
        # Run the workflow
        result = self.app.invoke(initial_state)
        
        # Save the results
        output_dir = "output"
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        if result.get("resume_analysis"):
            write_json_file(f"{output_dir}/resume_analysis.json", result["resume_analysis"])
        
        if result.get("job_analysis"):
            write_json_file(f"{output_dir}/job_analysis.json", result["job_analysis"])
        
        if result.get("tailored_resume"):
            with open(f"{output_dir}/tailored_resume.tex", "w", encoding="utf-8") as f:
                f.write(result["tailored_resume"])
        
        return result