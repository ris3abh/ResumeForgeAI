from typing import Dict, Any, List, Optional
import json

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from workflow.state import GraphState
from utils.file_utils import load_phase_config, read_json_file, write_json_file, read_text_file

# Import all agents
from agents.resume_analyzer import ResumeAnalyzerAgent
from agents.job_analyzer import JobAnalyzerAgent
from agents.orchestrator import OrchestratorAgent
from agents.work_experience_agent import WorkExperienceAgent
from agents.skills_agent import SkillsAgent
from agents.latex_validator import LaTeXValidatorAgent
from agents.compliance_agent import ComplianceAgent
from agents.resume_generator import ResumeGeneratorAgent


class ResumeAutomationWorkflow:
    """LangGraph workflow for resume automation."""
    
    def __init__(self):
        """Initialize the workflow."""
        # Load configuration
        self.phases_config = load_phase_config()
        
        # Initialize agents
        self.resume_analyzer = ResumeAnalyzerAgent()
        self.job_analyzer = JobAnalyzerAgent()
        self.orchestrator = OrchestratorAgent()
        self.work_experience_agent = WorkExperienceAgent()
        self.skills_agent = SkillsAgent()
        self.latex_validator = LaTeXValidatorAgent()
        self.compliance_agent = ComplianceAgent()
        self.resume_generator = ResumeGeneratorAgent()
        
        # Build the workflow graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        # Create the graph with a different config for messages
        workflow = StateGraph(GraphState)
        
        # Configure the graph to handle list updates properly
        workflow.set_list_option("messages", "append")
        
        # Create a list of enabled phases
        enabled_phases = [phase for phase in self.phases_config["phases"] if phase.get("enabled") is not False]
        enabled_phase_ids = [phase["id"] for phase in enabled_phases]
        
        # Add nodes for each enabled phase
        for phase in enabled_phases:
            phase_id = phase["id"]
            
            if phase_id == "phase_resume_analysis":
                workflow.add_node(phase_id, self._run_resume_analysis)
            elif phase_id == "phase_job_description_analysis":
                workflow.add_node(phase_id, self._run_job_analysis)
            elif phase_id == "phase_orchestration":
                workflow.add_node(phase_id, self._run_orchestration)
            elif phase_id == "phase_work_experience_customization":
                workflow.add_node(phase_id, self._run_work_experience_customization)
            elif phase_id == "phase_work_experience_validation":
                workflow.add_node(phase_id, self._run_work_experience_validation)
            elif phase_id == "phase_skills_customization":
                workflow.add_node(phase_id, self._run_skills_customization)
            elif phase_id == "phase_skills_validation":
                workflow.add_node(phase_id, self._run_skills_validation)
            elif phase_id == "phase_compliance_verification":
                workflow.add_node(phase_id, self._run_compliance_verification)
            elif phase_id == "phase_resume_generation":
                workflow.add_node(phase_id, self._run_resume_generation)
        
        # Add conditional edges
        # Only add edges for nodes that are actually in the graph
        for phase in enabled_phases:
            phase_id = phase["id"]
            next_phase = phase.get("next")
            
            if next_phase == "end":
                workflow.add_edge(phase_id, END)
            elif next_phase in enabled_phase_ids:
                workflow.add_edge(phase_id, next_phase)
        
        # Add error handling edges
        for phase_id in enabled_phase_ids:
            # Add conditional edge for error handling
            workflow.add_conditional_edges(
                phase_id,
                self._handle_error,
                {
                    "error": END,
                    "continue": phase_id  # No change, stays on the same node
                }
            )
        
        # Set the entry point to the first enabled phase
        if enabled_phase_ids:
            workflow.set_entry_point(enabled_phase_ids[0])
        
        return workflow
    
    def _handle_error(self, state: GraphState) -> str:
        """Handle errors in the workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next state transition
        """
        if state.get("error"):
            return "error"
        return "continue"
    
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
            
            # Create new message
            analysis_summary = f"Resume analysis complete. Identified {len(analysis_result.get('sections', []))} sections."
            new_message = AIMessage(content=analysis_summary, name="ResumeAnalyzer")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "resume_analysis": analysis_result,
                "current_phase": "phase_resume_analysis",
                "completed_phases": state["completed_phases"] + ["Resume Analysis"],
                "next": "phase_job_description_analysis",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in resume analysis: {str(e)}", name="ResumeAnalyzer")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_resume_analysis",
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
            
            # Create new message
            analysis_summary = f"Job description analysis complete. Found {len(analysis_result.get('structured_recommendations', {}).get('key_requirements', []))} key requirements."
            new_message = AIMessage(content=analysis_summary, name="JobAnalyzer")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "job_analysis": analysis_result,
                "current_phase": "phase_job_description_analysis",
                "completed_phases": state["completed_phases"] + ["Job Description Analysis"],
                "next": "phase_orchestration",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in job description analysis: {str(e)}", name="JobAnalyzer")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_job_description_analysis",
                "error": f"Error in job description analysis: {str(e)}",
                "next": "error"
            }
    
    def _run_orchestration(self, state: GraphState) -> GraphState:
        """Run orchestration phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get the resume and job analyses
            resume_analysis = state["resume_analysis"]
            job_analysis = state["job_analysis"]
            
            # Create a task plan
            task_plan = self.orchestrator.create_task_plan(resume_analysis, job_analysis)
            
            # Create agent assignments
            agents = {
                "work_experience_agent": self.work_experience_agent,
                "skills_agent": self.skills_agent,
                "latex_validator": self.latex_validator,
                "compliance_agent": self.compliance_agent
            }
            
            agent_assignments = self.orchestrator.assign_tasks(task_plan["plan"], agents)
            
            # Create new message
            orchestration_summary = f"Orchestration complete. Created task plan with {len(task_plan['plan'].get('sections_to_customize', []))} sections to customize."
            new_message = AIMessage(content=orchestration_summary, name="Orchestrator")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "task_plan": task_plan["plan"],
                "agent_assignments": agent_assignments,
                "current_phase": "phase_orchestration",
                "completed_phases": state["completed_phases"] + ["Customization Orchestration"],
                "next": "phase_work_experience_customization",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in orchestration: {str(e)}", name="Orchestrator")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_orchestration",
                "error": f"Error in orchestration: {str(e)}",
                "next": "error"
            }
    
    def _run_work_experience_customization(self, state: GraphState) -> GraphState:
        """Run work experience customization phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            job_analysis = state["job_analysis"]
            resume_analysis = state["resume_analysis"]
            task_plan = state["task_plan"]
            
            # Read the resume content
            resume_content = read_text_file(resume_file)
            
            # Customize the work experience section
            customization_result = self.work_experience_agent.customize(
                resume_content,
                job_analysis,
                resume_analysis
            )
            
            # Create new message
            customization_summary = "Work experience customization complete."
            new_message = AIMessage(content=customization_summary, name="WorkExperienceAgent")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "work_experience_customization": customization_result,
                "current_phase": "phase_work_experience_customization",
                "completed_phases": state["completed_phases"] + ["Work Experience Customization"],
                "next": "phase_work_experience_validation",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in work experience customization: {str(e)}", name="WorkExperienceAgent")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_work_experience_customization",
                "error": f"Error in work experience customization: {str(e)}",
                "next": "error"
            }
    
    def _run_work_experience_validation(self, state: GraphState) -> GraphState:
        """Run work experience validation phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            work_experience_customization = state["work_experience_customization"]
            
            # Read the original resume content
            original_content = read_text_file(resume_file)
            
            # Get the customized section
            customized_section = work_experience_customization.get("customized_section", "")
            
            # Validate the customized section
            validation_result = self.latex_validator.validate(
                original_content,
                customized_section,
                "EXPERIENCE"
            )
            
            # If there are errors, refine the customization
            if not validation_result.get("is_valid", False) or validation_result.get("errors", []):
                # Refine the customized section
                job_analysis = state["job_analysis"]
                refinement_result = self.work_experience_agent.refine(
                    customized_section,
                    validation_result,
                    job_analysis
                )
                
                # Update the customization result
                work_experience_customization["customized_section"] = refinement_result.get("refined_section", customized_section)
                work_experience_customization["refinement"] = refinement_result
            
            # Create new message
            validation_summary = f"Work experience validation complete. {'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. {len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings."
            new_message = AIMessage(content=validation_summary, name="LaTeXValidator")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "work_experience_validation": validation_result,
                "work_experience_customization": work_experience_customization,  # Updated with refinements if needed
                "current_phase": "phase_work_experience_validation",
                "completed_phases": state["completed_phases"] + ["Work Experience Validation"],
                "next": "phase_skills_customization",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in work experience validation: {str(e)}", name="LaTeXValidator")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_work_experience_validation",
                "error": f"Error in work experience validation: {str(e)}",
                "next": "error"
            }
    
    def _run_skills_customization(self, state: GraphState) -> GraphState:
        """Run skills customization phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            job_analysis = state["job_analysis"]
            resume_analysis = state["resume_analysis"]
            task_plan = state["task_plan"]
            
            # Read the resume content
            resume_content = read_text_file(resume_file)
            
            # Customize the skills section
            customization_result = self.skills_agent.customize(
                resume_content,
                job_analysis,
                resume_analysis
            )
            
            # Create new message
            customization_summary = "Skills customization complete."
            new_message = AIMessage(content=customization_summary, name="SkillsAgent")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "skills_customization": customization_result,
                "current_phase": "phase_skills_customization",
                "completed_phases": state["completed_phases"] + ["Skills Customization"],
                "next": "phase_skills_validation",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in skills customization: {str(e)}", name="SkillsAgent")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_skills_customization",
                "error": f"Error in skills customization: {str(e)}",
                "next": "error"
            }
    
    def _run_skills_validation(self, state: GraphState) -> GraphState:
        """Run skills validation phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            skills_customization = state["skills_customization"]
            
            # Read the original resume content
            original_content = read_text_file(resume_file)
            
            # Get the customized section
            customized_section = skills_customization.get("customized_section", "")
            
            # Validate the customized section
            validation_result = self.latex_validator.validate(
                original_content,
                customized_section,
                "TECHNICAL SKILLS"
            )
            
            # If there are errors, refine the customization
            if not validation_result.get("is_valid", False) or validation_result.get("errors", []):
                # Refine the customized section
                job_analysis = state["job_analysis"]
                refinement_result = self.skills_agent.refine(
                    customized_section,
                    validation_result,
                    job_analysis
                )
                
                # Update the customization result
                skills_customization["customized_section"] = refinement_result.get("refined_section", customized_section)
                skills_customization["refinement"] = refinement_result
            
            # Create new message
            validation_summary = f"Skills validation complete. {'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. {len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings."
            new_message = AIMessage(content=validation_summary, name="LaTeXValidator")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "skills_validation": validation_result,
                "skills_customization": skills_customization,  # Updated with refinements if needed
                "current_phase": "phase_skills_validation",
                "completed_phases": state["completed_phases"] + ["Skills Validation"],
                "next": "phase_compliance_verification",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in skills validation: {str(e)}", name="LaTeXValidator")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_skills_validation",
                "error": f"Error in skills validation: {str(e)}",
                "next": "error"
            }
    
    def _run_compliance_verification(self, state: GraphState) -> GraphState:
        """Run compliance verification phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get required inputs
            job_analysis = state["job_analysis"]
            work_experience_customization = state["work_experience_customization"]
            skills_customization = state["skills_customization"]
            
            # Create a dictionary of customized sections
            customized_sections = {
                "EXPERIENCE": work_experience_customization.get("customized_section", ""),
                "TECHNICAL SKILLS": skills_customization.get("customized_section", "")
            }
            
            # Verify compliance
            verification_result = self.compliance_agent.verify(
                customized_sections,
                job_analysis
            )
            
            # Get improvement suggestions if compliance score is below threshold
            if verification_result.get("compliance_score", 0) < 85:
                improvement_result = self.compliance_agent.suggest_improvements(
                    verification_result,
                    customized_sections
                )
                verification_result["improvements"] = improvement_result
            
            # Create new message
            verification_summary = f"Compliance verification complete. Compliance score: {verification_result.get('compliance_score', 0)}/100. {len(verification_result.get('missing_requirements', []))} missing requirements, {len(verification_result.get('missing_keywords', []))} missing keywords."
            new_message = AIMessage(content=verification_summary, name="ComplianceAgent")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "compliance_verification": verification_result,
                "current_phase": "phase_compliance_verification",
                "completed_phases": state["completed_phases"] + ["Compliance Verification"],
                "next": "phase_resume_generation",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in compliance verification: {str(e)}", name="ComplianceAgent")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_compliance_verification",
                "error": f"Error in compliance verification: {str(e)}",
                "next": "error"
            }
    
    def _run_resume_generation(self, state: GraphState) -> GraphState:
        """Run resume generation phase.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            work_experience_customization = state["work_experience_customization"]
            skills_customization = state["skills_customization"]
            compliance_verification = state["compliance_verification"]
            
            # Create a dictionary of customized sections
            customized_sections = {
                "EXPERIENCE": work_experience_customization.get("customized_section", ""),
                "TECHNICAL SKILLS": skills_customization.get("customized_section", "")
            }
            
            # Generate the tailored resume
            generation_result = self.resume_generator.generate(
                resume_file,
                customized_sections,
                compliance_verification
            )
            
            # Save the tailored resume to a file
            output_file = "output/tailored_resume.tex"
            self.resume_generator.save_resume(generation_result["final_resume"], output_file)
            
            # Create new message
            generation_summary = f"Resume generation complete. Tailored resume saved to {output_file}."
            new_message = AIMessage(content=generation_summary, name="ResumeGenerator")
            
            # Create a new state with updated values
            return {
                **state,
                "messages": state["messages"] + [new_message],  # Properly extend the messages list
                "tailored_resume": generation_result["final_resume"],
                "resume_generation": generation_result,
                "current_phase": "phase_resume_generation",
                "completed_phases": state["completed_phases"] + ["Resume Generation"],
                "next": "end",
                "error": None
            }
        except Exception as e:
            # Create error message
            error_message = AIMessage(content=f"Error in resume generation: {str(e)}", name="ResumeGenerator")
            
            # Return state with error
            return {
                **state,
                "messages": state["messages"] + [error_message],  # Properly extend the messages list
                "current_phase": "phase_resume_generation",
                "error": f"Error in resume generation: {str(e)}",
                "next": "error"
            }
    
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
            "messages": [],  # Start with an empty list of messages
            "current_phase": "",
            "completed_phases": [],
            "resume_file": resume_file,
            "job_description_file": job_description_file,
            "resume_analysis": None,
            "job_analysis": None,
            "task_plan": None,
            "agent_assignments": None,
            "work_experience_customization": None,
            "work_experience_validation": None,
            "skills_customization": None,
            "skills_validation": None,
            "compliance_verification": None,
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
        
        if result.get("task_plan"):
            write_json_file(f"{output_dir}/task_plan.json", result["task_plan"])
        
        if result.get("compliance_verification"):
            write_json_file(f"{output_dir}/compliance_verification.json", result["compliance_verification"])
        
        if result.get("tailored_resume"):
            with open(f"{output_dir}/tailored_resume.tex", "w", encoding="utf-8") as f:
                f.write(result["tailored_resume"])
        return result