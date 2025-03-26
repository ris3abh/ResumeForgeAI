from typing import Dict, Any, List, Optional, Literal
import json
import os
import logging
import concurrent.futures
import time

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

# Set up logging
logger = logging.getLogger("ResumeForgeAI.Graph")

class ResumeAutomationWorkflow:
    """LangGraph workflow for resume automation."""
    
    def __init__(self, show_agent_messages=False, early_exit_compliance_score=90, enable_parallel=True, verbose=False):
        """Initialize the workflow."""
        # Load configuration
        self.phases_config = load_phase_config()
        
        # Configuration options
        self.show_agent_messages = show_agent_messages
        self.early_exit_compliance_score = early_exit_compliance_score
        self.enable_parallel = enable_parallel
        self.verbose = verbose
        
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
    
    def _print_agent_message(self, agent_name, content, is_response=False):
        """Print agent message if show_agent_messages is enabled."""
        if self.show_agent_messages:
            if is_response:
                print(f"\n\033[1;36m[{agent_name} RESPONSE]\033[0m")
            else:
                print(f"\n\033[1;34m[{agent_name} REQUEST]\033[0m")
            
            # Print the content with a max length
            if isinstance(content, str):
                # Truncate long content for display
                if len(content) > 1000 and not self.verbose:
                    print(f"{content[:1000]}...\n[content truncated, set --verbose for full output]")
                else:
                    print(f"{content}")
            else:
                print(f"{content}")
            
            print("\033[1;30m" + "-" * 80 + "\033[0m")
    
    def _build_graph(self) -> StateGraph:
        # Create the state graph
        workflow = StateGraph(GraphState)
        
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
        
        # Add conditional edges with compliance early exit
        for phase in enabled_phases:
            phase_id = phase["id"]
            next_phase = phase.get("next")
            
            if phase_id == "phase_compliance_verification":
                # Add compliance-based conditional routing
                def compliance_router(state):
                    # Check for early exit based on compliance score
                    if state.get("error") is not None:
                        return "error"
                    
                    compliance_score = state.get("compliance_verification", {}).get("compliance_score", 0)
                    logger.info(f"Compliance score: {compliance_score} (threshold: {self.early_exit_compliance_score})")
                    
                    if compliance_score >= self.early_exit_compliance_score:
                        logger.info(f"Compliance score {compliance_score} meets threshold {self.early_exit_compliance_score}, proceeding to resume generation")
                        return "proceed_to_generation"
                    else:
                        logger.info(f"Compliance score {compliance_score} below threshold {self.early_exit_compliance_score}, will improve resume")
                        return "continue_normal_flow"
                
                workflow.add_conditional_edges(
                    phase_id,
                    compliance_router,
                    {
                        "error": END,
                        "proceed_to_generation": "phase_resume_generation",
                        "continue_normal_flow": next_phase if next_phase in enabled_phase_ids else END
                    }
                )
            else:
                # Standard edges for non-compliance phases
                if next_phase == "end":
                    workflow.add_edge(phase_id, END)
                elif next_phase in enabled_phase_ids:
                    workflow.add_edge(phase_id, next_phase)
        
        # Add error handling edges
        for phase_id in enabled_phase_ids:
            # For each phase, create a specific error handler
            def create_error_handler(phase):
                def error_handler(state):
                    has_error = state.get("error") is not None
                    if has_error:
                        return "error"
                    return "continue"
                return error_handler
            
            # Register the conditional edge if not already added by compliance routing
            if phase_id != "phase_compliance_verification":
                workflow.add_conditional_edges(
                    phase_id,
                    create_error_handler(phase_id),
                    {
                        "error": END,
                        "continue": phase_id  # No change, stays on the same node
                    }
                )
        
        # Set the entry point to the first enabled phase
        if enabled_phase_ids:
            workflow.set_entry_point(enabled_phase_ids[0])
        
        return workflow
    
    def _run_resume_analysis(self, state: GraphState) -> Dict[str, Any]:
        """Run resume analysis phase."""
        try:
            # Get the resume file path
            resume_file = state["resume_file"]
            
            # Check if we have cached resume analysis
            if state.get("cached_resume_analysis"):
                logger.info("Using cached resume analysis")
                analysis_result = state["cached_resume_analysis"]
                analysis_source = "cache"
            else:
                # Show the resume analyzer request
                self._print_agent_message("ResumeAnalyzer", f"Analyzing resume file: {resume_file}")
                
                # Run the analysis
                start_time = time.time()
                analysis_result = self.resume_analyzer.analyze(resume_file)
                duration = time.time() - start_time
                
                analysis_source = "new analysis"
                logger.info(f"Resume analysis completed in {duration:.2f} seconds")
            
            # Show the resume analyzer response
            self._print_agent_message(
                "ResumeAnalyzer", 
                f"Analysis complete ({analysis_source}). Identified {len(analysis_result.get('sections', []))} sections.",
                is_response=True
            )
            
            # Create new message
            analysis_summary = f"Resume analysis complete. Identified {len(analysis_result.get('sections', []))} sections."
            new_message = AIMessage(content=analysis_summary, name="ResumeAnalyzer")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],  # List will be combined with existing messages
                "resume_analysis": analysis_result,
                "current_phase": "phase_resume_analysis",
                "completed_phases": ["Resume Analysis"],
                "next": "phase_job_description_analysis",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in resume analysis: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in resume analysis: {str(e)}", name="ResumeAnalyzer")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_resume_analysis",
                "error": f"Error in resume analysis: {str(e)}",
                "next": "error"
            }
    
    def _run_job_analysis(self, state: GraphState) -> Dict[str, Any]:
        """Run job description analysis phase."""
        try:
            # Get the job description file path and resume analysis
            job_description_file = state["job_description_file"]
            resume_analysis = state["resume_analysis"]
            
            # Show the job analyzer request
            job_desc_content = read_text_file(job_description_file)
            prompt = f"Analyzing job description ({len(job_desc_content)} chars) with {len(resume_analysis.get('sections', []))} identified resume sections"
            self._print_agent_message("JobAnalyzer", prompt)
            
            # Run the analysis
            start_time = time.time()
            analysis_result = self.job_analyzer.analyze(job_description_file, resume_analysis)
            duration = time.time() - start_time
            
            logger.info(f"Job analysis completed in {duration:.2f} seconds")
            
            # Show the job analyzer response
            key_requirements = analysis_result.get('structured_recommendations', {}).get('key_requirements', [])
            keywords = analysis_result.get('structured_recommendations', {}).get('keywords', [])
            response_summary = f"Analysis complete. Found {len(key_requirements)} key requirements and {len(keywords)} keywords."
            self._print_agent_message("JobAnalyzer", response_summary, is_response=True)
            
            # Create new message
            analysis_summary = f"Job description analysis complete. Found {len(key_requirements)} key requirements."
            new_message = AIMessage(content=analysis_summary, name="JobAnalyzer")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "job_analysis": analysis_result,
                "current_phase": "phase_job_description_analysis",
                "completed_phases": ["Job Description Analysis"],
                "next": "phase_orchestration",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in job description analysis: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in job description analysis: {str(e)}", name="JobAnalyzer")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_job_description_analysis",
                "error": f"Error in job description analysis: {str(e)}",
                "next": "error"
            }
    
    def _run_orchestration(self, state: GraphState) -> Dict[str, Any]:
        """Run orchestration phase."""
        try:
            # Get the resume and job analyses
            resume_analysis = state["resume_analysis"]
            job_analysis = state["job_analysis"]
            
            # Show orchestration request
            orchestration_request = (
                f"Creating customization plan based on resume analysis with {len(resume_analysis.get('sections', []))} sections " +
                f"and job analysis with {len(job_analysis.get('structured_recommendations', {}).get('key_requirements', []))} requirements"
            )
            self._print_agent_message("Orchestrator", orchestration_request)
            
            # Create a task plan
            start_time = time.time()
            task_plan = self.orchestrator.create_task_plan(resume_analysis, job_analysis)
            plan_duration = time.time() - start_time
            
            # Show task plan response
            plan_response = (
                f"Task plan created in {plan_duration:.2f} seconds.\n" +
                f"Sections to customize: {', '.join(task_plan['plan'].get('sections_to_customize', []))}\n" +
                f"Priorities: {', '.join(task_plan['plan'].get('customization_priorities', []))}"
            )
            self._print_agent_message("Orchestrator", plan_response, is_response=True)
            
            # Show agent assignment request
            self._print_agent_message("Orchestrator", "Assigning tasks to specialized agents")
            
            # Create agent assignments
            start_time = time.time()
            agents = {
                "work_experience_agent": self.work_experience_agent,
                "skills_agent": self.skills_agent,
                "latex_validator": self.latex_validator,
                "compliance_agent": self.compliance_agent
            }
            
            agent_assignments = self.orchestrator.assign_tasks(task_plan["plan"], agents)
            assignment_duration = time.time() - start_time
            
            # Show assignments response
            assignments_response = f"Agent assignments created in {assignment_duration:.2f} seconds for {len(agent_assignments)} agents"
            self._print_agent_message("Orchestrator", assignments_response, is_response=True)
            
            # Create new message
            orchestration_summary = f"Orchestration complete. Created task plan with {len(task_plan['plan'].get('sections_to_customize', []))} sections to customize."
            new_message = AIMessage(content=orchestration_summary, name="Orchestrator")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "task_plan": task_plan["plan"],
                "agent_assignments": agent_assignments,
                "current_phase": "phase_orchestration",
                "completed_phases": ["Customization Orchestration"],
                "next": "phase_work_experience_customization",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in orchestration: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in orchestration: {str(e)}", name="Orchestrator")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_orchestration",
                "error": f"Error in orchestration: {str(e)}",
                "next": "error"
            }
    
    def _run_work_experience_customization(self, state: GraphState) -> Dict[str, Any]:
        """Run work experience customization phase."""
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            job_analysis = state["job_analysis"]
            resume_analysis = state["resume_analysis"]
            task_plan = state["task_plan"]
            
            # Read the resume content
            resume_content = read_text_file(resume_file)
            
            # If parallel processing is enabled, run both customization agents together
            if self.enable_parallel:
                logger.info("Starting parallel customization of work experience and skills sections")
                
                # Show the work experience customization request
                self._print_agent_message("WorkExperienceAgent", "Customizing work experience section based on job requirements")
                
                def customize_work_experience():
                    start_time = time.time()
                    result = self.work_experience_agent.customize(resume_content, job_analysis, resume_analysis)
                    duration = time.time() - start_time
                    logger.info(f"Work experience customization completed in {duration:.2f} seconds")
                    return result, duration
                
                def customize_skills():
                    start_time = time.time()
                    result = self.skills_agent.customize(resume_content, job_analysis, resume_analysis)
                    duration = time.time() - start_time
                    logger.info(f"Skills customization completed in {duration:.2f} seconds")
                    return result, duration
                
                # Execute both tasks in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_work = executor.submit(customize_work_experience)
                    future_skills = executor.submit(customize_skills)
                    
                    # Get results (this will block until both are done)
                    work_experience_result, work_duration = future_work.result()
                    skills_result, skills_duration = future_skills.result()
                
                # Store the skills result in the state to avoid redundant processing later
                state["skills_customization"] = skills_result
                
                # Print responses
                self._print_agent_message(
                    "WorkExperienceAgent", 
                    f"Work experience customization complete in {work_duration:.2f} seconds",
                    is_response=True
                )
                self._print_agent_message(
                    "SkillsAgent", 
                    f"Skills customization complete in {skills_duration:.2f} seconds",
                    is_response=True
                )
                
                customization_result = work_experience_result
            else:
                # Sequential processing - only customize work experience now
                self._print_agent_message("WorkExperienceAgent", "Customizing work experience section based on job requirements")
                
                start_time = time.time()
                customization_result = self.work_experience_agent.customize(
                    resume_content,
                    job_analysis,
                    resume_analysis
                )
                duration = time.time() - start_time
                
                self._print_agent_message(
                    "WorkExperienceAgent", 
                    f"Work experience customization complete in {duration:.2f} seconds",
                    is_response=True
                )
            
            # Create new message
            customization_summary = "Work experience customization complete."
            new_message = AIMessage(content=customization_summary, name="WorkExperienceAgent")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "work_experience_customization": customization_result,
                "current_phase": "phase_work_experience_customization",
                "completed_phases": ["Work Experience Customization"],
                "next": "phase_work_experience_validation",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in work experience customization: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in work experience customization: {str(e)}", name="WorkExperienceAgent")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_work_experience_customization",
                "error": f"Error in work experience customization: {str(e)}",
                "next": "error"
            }
    
    def _run_work_experience_validation(self, state: GraphState) -> Dict[str, Any]:
        """Run work experience validation phase."""
        try:
            # Get required inputs
            resume_file = state["resume_file"]
            work_experience_customization = state["work_experience_customization"]
            
            # Read the original resume content
            original_content = read_text_file(resume_file)
            
            # Get the customized section
            customized_section = work_experience_customization.get("customized_section", "")
            
            # If parallel processing is enabled, run both validations together
            if self.enable_parallel and state.get("skills_customization"):
                logger.info("Starting parallel validation of work experience and skills sections")
                
                # Show the validation requests
                self._print_agent_message("LaTeXValidator", "Validating work experience section")
                self._print_agent_message("LaTeXValidator", "Validating skills section")
                
                skills_customization = state.get("skills_customization", {})
                skills_section = skills_customization.get("customized_section", "")
                
                def validate_work_experience():
                    start_time = time.time()
                    result = self.latex_validator.validate(original_content, customized_section, "EXPERIENCE")
                    duration = time.time() - start_time
                    logger.info(f"Work experience validation completed in {duration:.2f} seconds")
                    return result, duration
                
                def validate_skills():
                    start_time = time.time()
                    result = self.latex_validator.validate(original_content, skills_section, "TECHNICAL SKILLS")
                    duration = time.time() - start_time
                    logger.info(f"Skills validation completed in {duration:.2f} seconds")
                    return result, duration
                
                # Execute both validations in parallel
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_work = executor.submit(validate_work_experience)
                    future_skills = executor.submit(validate_skills)
                    
                    # Get results
                    validation_result, work_duration = future_work.result()
                    skills_validation_result, skills_duration = future_skills.result()
                
                # Store the skills validation result
                state["skills_validation"] = skills_validation_result
                
                # Show validation responses
                self._print_agent_message(
                    "LaTeXValidator", 
                    f"Work experience validation complete in {work_duration:.2f} seconds: " +
                    f"{'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. " +
                    f"{len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings.",
                    is_response=True
                )
                
                self._print_agent_message(
                    "LaTeXValidator", 
                    f"Skills validation complete in {skills_duration:.2f} seconds: " +
                    f"{'Valid' if skills_validation_result.get('is_valid', False) else 'Invalid'} LaTeX. " +
                    f"{len(skills_validation_result.get('errors', []))} errors, {len(skills_validation_result.get('warnings', []))} warnings.",
                    is_response=True
                )
                
                # Process both validation results in parallel if there are errors
                needs_work_refinement = not validation_result.get("is_valid", False) or validation_result.get("errors", [])
                needs_skills_refinement = not skills_validation_result.get("is_valid", False) or skills_validation_result.get("errors", [])
                
                if needs_work_refinement or needs_skills_refinement:
                    logger.info("Starting parallel refinement based on validation feedback")
                    job_analysis = state["job_analysis"]
                    
                    def refine_work_experience():
                        if needs_work_refinement:
                            start_time = time.time()
                            result = self.work_experience_agent.refine(customized_section, validation_result, job_analysis)
                            duration = time.time() - start_time
                            logger.info(f"Work experience refinement completed in {duration:.2f} seconds")
                            return result, duration
                        return None, 0
                    
                    def refine_skills():
                        if needs_skills_refinement:
                            start_time = time.time()
                            result = self.skills_agent.refine(skills_section, skills_validation_result, job_analysis)
                            duration = time.time() - start_time
                            logger.info(f"Skills refinement completed in {duration:.2f} seconds")
                            return result, duration
                        return None, 0
                    
                    # Execute both refinements in parallel
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future_work_refine = executor.submit(refine_work_experience)
                        future_skills_refine = executor.submit(refine_skills)
                        
                        # Get results
                        work_refinement_result, work_refinement_duration = future_work_refine.result()
                        skills_refinement_result, skills_refinement_duration = future_skills_refine.result()
                    
                    # Update work experience if refinement was needed
                    if needs_work_refinement and work_refinement_result:
                        work_experience_customization_updated = dict(work_experience_customization)
                        work_experience_customization_updated["customized_section"] = work_refinement_result.get("refined_section", customized_section)
                        work_experience_customization_updated["refinement"] = work_refinement_result
                        
                        self._print_agent_message(
                            "WorkExperienceAgent", 
                            f"Work experience refinement complete in {work_refinement_duration:.2f} seconds",
                            is_response=True
                        )
                    else:
                        work_experience_customization_updated = work_experience_customization
                    
                    # Update skills if refinement was needed
                    if needs_skills_refinement and skills_refinement_result:
                        skills_customization_updated = dict(skills_customization)
                        skills_customization_updated["customized_section"] = skills_refinement_result.get("refined_section", skills_section)
                        skills_customization_updated["refinement"] = skills_refinement_result
                        state["skills_customization"] = skills_customization_updated
                        
                        self._print_agent_message(
                            "SkillsAgent", 
                            f"Skills refinement complete in {skills_refinement_duration:.2f} seconds",
                            is_response=True
                        )
                else:
                    work_experience_customization_updated = work_experience_customization
            else:
                # Sequential processing
                self._print_agent_message("LaTeXValidator", "Validating work experience section")
                
                # Validate the customized section
                start_time = time.time()
                validation_result = self.latex_validator.validate(
                    original_content,
                    customized_section,
                    "EXPERIENCE"
                )
                duration = time.time() - start_time
                
                # Show validation response
                self._print_agent_message(
                    "LaTeXValidator", 
                    f"Work experience validation complete in {duration:.2f} seconds: " +
                    f"{'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. " +
                    f"{len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings.",
                    is_response=True
                )
                
                # If there are errors, refine the customization
                if not validation_result.get("is_valid", False) or validation_result.get("errors", []):
                    # Show refinement request
                    self._print_agent_message("WorkExperienceAgent", "Refining work experience section based on validation feedback")
                    
                    # Refine the customized section
                    job_analysis = state["job_analysis"]
                    start_time = time.time()
                    refinement_result = self.work_experience_agent.refine(
                        customized_section,
                        validation_result,
                        job_analysis
                    )
                    refinement_duration = time.time() - start_time
                    
                    # Show refinement response
                    self._print_agent_message(
                        "WorkExperienceAgent", 
                        f"Work experience refinement complete in {refinement_duration:.2f} seconds",
                        is_response=True
                    )
                    
                    # Update the customization result
                    work_experience_customization_updated = dict(work_experience_customization)
                    work_experience_customization_updated["customized_section"] = refinement_result.get("refined_section", customized_section)
                    work_experience_customization_updated["refinement"] = refinement_result
                else:
                    work_experience_customization_updated = work_experience_customization
            
            validation_summary = f"Work experience validation complete. {'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. {len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings."
            new_message = AIMessage(content=validation_summary, name="LaTeXValidator")
            
            # Determine next step based on parallel processing
            next_phase = "phase_compliance_verification" if self.enable_parallel and state.get("skills_validation") else "phase_skills_customization"
            completed_phases = ["Work Experience Validation"]
            
            # Add skills validation to completed phases if done in parallel
            if self.enable_parallel and state.get("skills_validation"):
                completed_phases.append("Skills Validation")
                completed_phases.append("Skills Customization")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "work_experience_validation": validation_result,
                "work_experience_customization": work_experience_customization_updated,
                "current_phase": "phase_work_experience_validation",
                "completed_phases": completed_phases,
                "next": next_phase,
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in work experience validation: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in work experience validation: {str(e)}", name="LaTeXValidator")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_work_experience_validation",
                "error": f"Error in work experience validation: {str(e)}",
                "next": "error"
            }
    
    def _run_skills_customization(self, state: GraphState) -> Dict[str, Any]:
        """Run skills customization phase."""
        try:
            # Check if skills customization was already done in parallel
            if self.enable_parallel and state.get("skills_customization"):
                logger.info("Using skills customization completed in parallel")
                customization_result = state["skills_customization"]
                
                # Create new message
                customization_summary = "Skills customization already completed in parallel."
                new_message = AIMessage(content=customization_summary, name="SkillsAgent")
            else:
                # Get required inputs
                resume_file = state["resume_file"]
                job_analysis = state["job_analysis"]
                resume_analysis = state["resume_analysis"]
                task_plan = state["task_plan"]
                
                # Read the resume content
                resume_content = read_text_file(resume_file)
                
                # Show the skills customization request
                self._print_agent_message("SkillsAgent", "Customizing skills section based on job requirements")
                
                # Customize the skills section
                start_time = time.time()
                customization_result = self.skills_agent.customize(
                    resume_content,
                    job_analysis,
                    resume_analysis
                )
                duration = time.time() - start_time
                
                # Show the skills customization response
                self._print_agent_message(
                    "SkillsAgent", 
                    f"Skills customization complete in {duration:.2f} seconds",
                    is_response=True
                )
                
                # Create new message
                customization_summary = "Skills customization complete."
                new_message = AIMessage(content=customization_summary, name="SkillsAgent")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "skills_customization": customization_result,
                "current_phase": "phase_skills_customization",
                "completed_phases": ["Skills Customization"],
                "next": "phase_skills_validation",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in skills customization: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in skills customization: {str(e)}", name="SkillsAgent")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_skills_customization",
                "error": f"Error in skills customization: {str(e)}",
                "next": "error"
            }
        

    def _run_skills_validation(self, state: GraphState) -> Dict[str, Any]:
        """Run skills validation phase."""
        try:
            # Check if skills validation was already done in parallel
            if self.enable_parallel and state.get("skills_validation"):
                logger.info("Using skills validation completed in parallel")
                validation_result = state["skills_validation"]
                skills_customization = state["skills_customization"]
                
                # Just reuse the results without doing validation again
                skills_customization_updated = skills_customization
                
                # Create new message
                validation_summary = f"Skills validation already completed in parallel. {'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. {len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings."
                new_message = AIMessage(content=validation_summary, name="LaTeXValidator")
            else:
                # Get required inputs
                resume_file = state["resume_file"]
                skills_customization = state["skills_customization"]
                
                # Read the original resume content
                original_content = read_text_file(resume_file)
                
                # Get the customized section
                customized_section = skills_customization.get("customized_section", "")
                
                # Show validation request
                self._print_agent_message("LaTeXValidator", "Validating skills section")
                
                # Validate the customized section
                start_time = time.time()
                validation_result = self.latex_validator.validate(
                    original_content,
                    customized_section,
                    "TECHNICAL SKILLS"
                )
                duration = time.time() - start_time
                
                # Show validation response
                self._print_agent_message(
                    "LaTeXValidator", 
                    f"Skills validation complete in {duration:.2f} seconds: " +
                    f"{'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. " +
                    f"{len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings.",
                    is_response=True
                )
                
                # If there are errors, refine the customization
                if not validation_result.get("is_valid", False) or validation_result.get("errors", []):
                    # Show refinement request
                    self._print_agent_message("SkillsAgent", "Refining skills section based on validation feedback")
                    
                    # Refine the customized section
                    job_analysis = state["job_analysis"]
                    start_time = time.time()
                    refinement_result = self.skills_agent.refine(
                        customized_section,
                        validation_result,
                        job_analysis
                    )
                    refinement_duration = time.time() - start_time
                    
                    # Show refinement response
                    self._print_agent_message(
                        "SkillsAgent", 
                        f"Skills refinement complete in {refinement_duration:.2f} seconds",
                        is_response=True
                    )
                    
                    # Update the customization result
                    skills_customization_updated = dict(skills_customization)
                    skills_customization_updated["customized_section"] = refinement_result.get("refined_section", customized_section)
                    skills_customization_updated["refinement"] = refinement_result
                else:
                    skills_customization_updated = skills_customization
                
                # Create new message
                validation_summary = f"Skills validation complete. {'Valid' if validation_result.get('is_valid', False) else 'Invalid'} LaTeX. {len(validation_result.get('errors', []))} errors, {len(validation_result.get('warnings', []))} warnings."
                new_message = AIMessage(content=validation_summary, name="LaTeXValidator")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "skills_validation": validation_result,
                "skills_customization": skills_customization_updated,
                "current_phase": "phase_skills_validation",
                "completed_phases": ["Skills Validation"],
                "next": "phase_compliance_verification",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in skills validation: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in skills validation: {str(e)}", name="LaTeXValidator")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_skills_validation",
                "error": f"Error in skills validation: {str(e)}",
                "next": "error"
            }
    
    def _run_compliance_verification(self, state: GraphState) -> Dict[str, Any]:
        """Run compliance verification phase."""
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
            
            # Show compliance verification request
            key_requirements = job_analysis.get("structured_recommendations", {}).get("key_requirements", [])
            keywords = job_analysis.get("structured_recommendations", {}).get("keywords", [])
            
            verification_request = f"Verifying compliance with {len(key_requirements)} job requirements and {len(keywords)} keywords"
            self._print_agent_message("ComplianceAgent", verification_request)
            
            # Verify compliance
            start_time = time.time()
            verification_result = self.compliance_agent.verify(
                customized_sections,
                job_analysis
            )
            duration = time.time() - start_time
            
            # Display compliance score and status
            compliance_score = verification_result.get("compliance_score", 0)
            req_compliance = verification_result.get("requirement_compliance_percentage", 0)
            kw_compliance = verification_result.get("keyword_compliance_percentage", 0)
            missing_reqs = verification_result.get("missing_requirements", [])
            missing_kws = verification_result.get("missing_keywords", [])
            
            verification_response = (
                f"Compliance verification complete in {duration:.2f} seconds.\n" +
                f"Overall compliance score: {compliance_score}/100\n" +
                f"Requirements compliance: {req_compliance:.1f}%\n" +
                f"Keywords compliance: {kw_compliance:.1f}%\n" +
                f"Missing requirements: {len(missing_reqs)}\n" +
                f"Missing keywords: {len(missing_kws)}"
            )
            self._print_agent_message("ComplianceAgent", verification_response, is_response=True)
            
            # Get improvement suggestions if compliance score is below threshold
            if compliance_score < self.early_exit_compliance_score:
                # Show suggestions request
                self._print_agent_message(
                    "ComplianceAgent", 
                    f"Compliance score {compliance_score} below threshold {self.early_exit_compliance_score}. Requesting improvement suggestions."
                )
                
                # Get improvement suggestions
                start_time = time.time()
                improvement_result = self.compliance_agent.suggest_improvements(
                    verification_result,
                    customized_sections
                )
                improvement_duration = time.time() - start_time
                
                # Show suggestions response
                suggestions_summary = f"Improvement suggestions generated in {improvement_duration:.2f} seconds."
                self._print_agent_message("ComplianceAgent", suggestions_summary, is_response=True)
                
                # Add suggestions to verification result
                verification_result["improvements"] = improvement_result
            else:
                # Show early exit message
                early_exit_msg = f"Compliance score {compliance_score} meets or exceeds threshold {self.early_exit_compliance_score}. No improvements needed."
                self._print_agent_message("ComplianceAgent", early_exit_msg, is_response=True)
            
            # Create new message
            verification_summary = f"Compliance verification complete. Compliance score: {verification_result.get('compliance_score', 0)}/100. {len(verification_result.get('missing_requirements', []))} missing requirements, {len(verification_result.get('missing_keywords', []))} missing keywords."
            new_message = AIMessage(content=verification_summary, name="ComplianceAgent")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "compliance_verification": verification_result,
                "current_phase": "phase_compliance_verification",
                "completed_phases": ["Compliance Verification"],
                "next": "phase_resume_generation",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in compliance verification: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in compliance verification: {str(e)}", name="ComplianceAgent")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_compliance_verification",
                "error": f"Error in compliance verification: {str(e)}",
                "next": "error"
            }
    
    def _run_resume_generation(self, state: GraphState) -> Dict[str, Any]:
        """Run resume generation phase."""
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
            
            # Show resume generation request
            compliance_score = compliance_verification.get("compliance_score", 0)
            generation_request = (
                f"Generating final tailored resume with compliance score: {compliance_score}/100.\n" +
                f"Customized sections: {', '.join(customized_sections.keys())}"
            )
            self._print_agent_message("ResumeGenerator", generation_request)
            
            # Generate the tailored resume
            start_time = time.time()
            generation_result = self.resume_generator.generate(
                resume_file,
                customized_sections,
                compliance_verification
            )
            duration = time.time() - start_time
            
            # Save the tailored resume to a file
            output_file = "output/tailored_resume.tex"
            self.resume_generator.save_resume(generation_result["final_resume"], output_file)
            
            # Show resume generation response
            generation_response = f"Resume generation complete in {duration:.2f} seconds. Tailored resume saved to {output_file}"
            self._print_agent_message("ResumeGenerator", generation_response, is_response=True)
            
            # Create new message
            generation_summary = f"Resume generation complete. Tailored resume saved to {output_file}."
            new_message = AIMessage(content=generation_summary, name="ResumeGenerator")
            
            # Return only the changes to the state
            return {
                "messages": [new_message],
                "tailored_resume": generation_result["final_resume"],
                "resume_generation": generation_result,
                "current_phase": "phase_resume_generation",
                "completed_phases": ["Resume Generation"],
                "next": "end",
                "error": None
            }
        except Exception as e:
            logger.error(f"Error in resume generation: {str(e)}")
            # Create error message
            error_message = AIMessage(content=f"Error in resume generation: {str(e)}", name="ResumeGenerator")
            
            # Return state with error
            return {
                "messages": [error_message],
                "current_phase": "phase_resume_generation",
                "error": f"Error in resume generation: {str(e)}",
                "next": "error"
            }
        
    def run(self, resume_file: str, job_description_file: str, cached_resume_analysis=None) -> Dict[str, Any]:
        """Run the workflow.
        
        Args:
            resume_file: Path to the LaTeX resume file
            job_description_file: Path to the job description file
            cached_resume_analysis: Optional cached resume analysis result
            
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
            "cached_resume_analysis": cached_resume_analysis,  # Add cached analysis if available
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
        try:
            start_time = time.time()
            logger.info(f"Starting workflow execution with {'' if self.enable_parallel else 'no '}parallel processing")
            result = self.app.invoke(initial_state)
            duration = time.time() - start_time
            logger.info(f"Workflow completed in {duration:.2f} seconds")
            
            # Save the results
            output_dir = "output"
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
            
            # Add timing information to the result
            result["workflow_duration_seconds"] = duration
            
            # Print workflow summary
            print(f"\n\n\033[1;32m[WORKFLOW COMPLETE]\033[0m")
            print(f"Total time: {duration:.2f} seconds")
            
            compliance_score = result.get("compliance_verification", {}).get("compliance_score", 0)
            if compliance_score >= self.early_exit_compliance_score:
                print(f"Compliance score: {compliance_score}/100 ✅ (meets or exceeds threshold of {self.early_exit_compliance_score})")
            else:
                print(f"Compliance score: {compliance_score}/100 ⚠️ (below threshold of {self.early_exit_compliance_score})")
            
            print(f"Output directory: {output_dir}")
            
            return result
        except Exception as e:
            # Handle any workflow execution errors
            logger.error(f"Error executing workflow: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return a basic error result
            return {
                "error": f"Workflow execution failed: {str(e)}",
                "completed_phases": []
            }
    