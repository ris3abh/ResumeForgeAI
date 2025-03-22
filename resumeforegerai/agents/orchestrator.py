from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage

from utils.file_utils import read_text_file, load_agent_config
from utils.openai_client import create_chat_openai

class OrchestratorAgent:
    """Agent for orchestrating the resume customization workflow.
    
    This agent coordinates the communication between all specialized agents,
    distributes tasks, and manages the overall customization process.
    """
    
    def __init__(self):
        """Initialize the orchestrator agent."""
        # Load agent configuration
        self.config = load_agent_config("orchestrator")
        
        # Initialize the model
        model_config = self.config["model"]
        self.model = create_chat_openai(
            model_name=model_config["name"],
            temperature=model_config["temperature"]
        )
        
        # Keep track of agent states
        self.agent_states = {}
    
    def create_task_plan(self, resume_analysis: Dict[str, Any], job_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customization plan based on resume and job analyses.
        
        Args:
            resume_analysis: Analysis of the resume structure
            job_analysis: Analysis of the job description
            
        Returns:
            Task plan with assignments for specialized agents
        """
        # Create a prompt for task planning
        prompt = self._create_task_planning_prompt(resume_analysis, job_analysis)
        
        # Get the plan from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Extract structured plan
        task_plan = self._extract_structured_plan(response.content)
        
        return {
            "plan": task_plan,
            "raw_planning": response.content
        }
    
    def assign_tasks(self, task_plan: Dict[str, Any], agents: Dict[str, Any]) -> Dict[str, Any]:
        """Assign tasks to specialized agents based on the task plan.
        
        Args:
            task_plan: The customization plan created earlier
            agents: Dictionary of available agent instances
            
        Returns:
            Task assignments with agent IDs and their specific tasks
        """
        # Extract tasks from the plan
        assignments = {}
        
        for agent_id, agent_tasks in task_plan.get("agent_tasks", {}).items():
            if agent_id in agents:
                assignments[agent_id] = {
                    "agent": agents[agent_id],
                    "tasks": agent_tasks
                }
        
        return assignments
    
    def integrate_agent_outputs(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate outputs from all specialized agents.
        
        Args:
            agent_outputs: Outputs from all agents
            
        Returns:
            Integrated results
        """
        # Create a prompt for integration
        agent_results = "\n\n".join([
            f"--- {agent_id} Output ---\n{output.get('result', '')}"
            for agent_id, output in agent_outputs.items()
        ])
        
        prompt = f"""
            {self.config.get('integration_prompt', 'You are the Orchestrator Agent responsible for integrating outputs from multiple specialized agents.')}

            I have received outputs from multiple specialized agents working on customizing a resume. 
            Please analyze these outputs and create an integrated result that maintains consistency and addresses any conflicts.

            {agent_results}

            Please provide your integrated result in a structured format with reasoning for any choices you made to resolve conflicts or inconsistencies.
            """
        
        # Get the integrated result from the LLM
        response = self.model.invoke([
            HumanMessage(content=prompt)
        ])
        
        # Store the agent outputs and the integrated result
        return {
            "agent_outputs": agent_outputs,
            "integrated_result": response.content
        }
    
    def _create_task_planning_prompt(self, resume_analysis: Dict[str, Any], job_analysis: Dict[str, Any]) -> str:
        """Create a prompt for task planning.
        
        Args:
            resume_analysis: Analysis of the resume structure
            job_analysis: Analysis of the job description
            
        Returns:
            Prompt for the LLM
        """
        # Extract key information for the prompt
        resume_sections = resume_analysis.get("sections", [])
        job_requirements = job_analysis.get("structured_recommendations", {}).get("key_requirements", [])
        
        sections_info = "\n".join([f"- {section.get('name', 'Unknown Section')}" for section in resume_sections])
        requirements_info = "\n".join([f"- {req}" for req in job_requirements])
        
        return f"""
            {self.config.get('system_prompt', 'You are the Orchestrator Agent responsible for planning and coordinating the resume customization process.')}

            I need to create a plan for customizing a resume based on the following analyses:

            RESUME SECTIONS:
            {sections_info}

            JOB REQUIREMENTS:
            {requirements_info}

            The following specialized agents are available to help:
            1. Work Experience Customization Agent: Can tailor work experience bullet points to highlight relevant experience
            2. Skills Customization Agent: Can optimize the skills section to match job requirements
            3. LaTeX Validation Agent: Can verify that LaTeX formatting is correct
            4. Compliance Verification Agent: Can check if all requirements are addressed

            Please create a detailed plan including:
            1. Which sections need customization and why
            2. Which agents should work on which sections
            3. The order in which agents should work
            4. How the agents should collaborate and share information

            Format your response as a structured plan that can be parsed programmatically.
            """
    
    def _extract_structured_plan(self, llm_response: str) -> Dict[str, Any]:
        """Extract a structured plan from the LLM response.
        
        Args:
            llm_response: Response from the LLM
            
        Returns:
            Structured plan
        """
        # Create a prompt to extract structured data
        extraction_prompt = f"""
            Based on your task planning response, please convert your plan into a JSON format with the following structure:
            1. sections_to_customize: List of section names that need customization
            2. customization_priorities: List of section names in priority order
            3. agent_tasks: Dictionary mapping agent_id to list of tasks
            4. collaboration_points: List of points where agents need to share information

            Please format your response ONLY as valid JSON with these fields.

            Your original planning response:
            {llm_response}
            """
        
        try:
            # Get structured data from the LLM
            extraction_response = self.model.invoke([
                HumanMessage(content=extraction_prompt)
            ])
            
            # Try to parse JSON from the response
            import json
            import re
            
            # Look for JSON block in the response
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', extraction_response.content)
            if json_match:
                json_str = json_match.group(1)
                try:
                    structured_data = json.loads(json_str)
                    return structured_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a basic structure
                    pass
        except Exception as e:
            pass
        
        # Fallback: return a simple structure
        return {
            "sections_to_customize": [],
            "customization_priorities": [],
            "agent_tasks": {},
            "collaboration_points": []
        }