# resumeai/resume_env.py
import os
import shutil
import time
from typing import Dict

class ResumeEnvConfig:
    def __init__(self, 
                 latex_output: bool,
                 clear_structure: bool,
                 with_memory: bool,
                 background_prompt: str):
        self.latex_output = latex_output  # Whether to output a LaTeX file
        self.clear_structure = clear_structure  # Whether to clear non-essential files in output directory
        self.with_memory = with_memory  # Whether to use memory in agent interactions
        self.background_prompt = background_prompt  # Background prompt added to every inquiry to LLM

    def __str__(self):
        string = ""
        string += f"ResumeEnvConfig.latex_output: {self.latex_output}\n"
        string += f"ResumeEnvConfig.clear_structure: {self.clear_structure}\n"
        string += f"ResumeEnvConfig.with_memory: {self.with_memory}\n"
        string += f"ResumeEnvConfig.background_prompt: {self.background_prompt}\n"
        return string

class ResumeEnv:
    def __init__(self, resume_env_config: ResumeEnvConfig):
        self.config = resume_env_config
        self.roster = []  # List of agent names
        self.memory = None  # Will be initialized if with_memory is True
        self.env_dict = {
            "directory": "",
            "resume_content": "",
            "job_description": "",
            "resume_work_experience": "",
            "resume_skills": "",
            "job_description_analysis": "",
            "updated_work_experience": "",
            "updated_skills": "",
            "quality_feedback": "",
            "updated_summary": "",
            "original_resume": "",
            "final_resume": ""
        }

    def set_directory(self, directory):
        """Set the output directory for the tailored resume."""
        self.env_dict['directory'] = directory
        
        # If directory exists and has content, create a backup
        if os.path.exists(directory) and len(os.listdir(directory)) > 0:
            new_directory = "{}.{}".format(directory, time.strftime("%Y%m%d%H%M%S", time.localtime()))
            shutil.copytree(directory, new_directory)
            print(f"{directory} Copied to {new_directory}")
        
        # Create or recreate the directory
        if os.path.exists(directory):
            shutil.rmtree(directory)
            os.mkdir(directory)
            print(f"{directory} Created")
        else:
            os.mkdir(directory)
            print(f"{directory} Created")

    def init_memory(self):
        """Initialize memory for the agents if enabled."""
        # This will be implemented if we add memory capabilities later
        # For now, we'll just create a placeholder
        if self.config.with_memory:
            memory_dir = os.path.join(os.getcwd(), "resumeai", "memory")
            if not os.path.exists(memory_dir):
                os.makedirs(memory_dir, exist_ok=True)
            print(f"Memory initialized in {memory_dir}")
        
    def recruit(self, agent_name: str):
        """Add an agent to the roster."""
        if agent_name not in self.roster:
            self.roster.append(agent_name)
            print(f"Recruited {agent_name}")

    def exist_employee(self, agent_name: str) -> bool:
        """Check if an agent is in the roster."""
        return agent_name in self.roster

    def print_employees(self):
        """Print all recruited agents."""
        print(f"Employees: {', '.join(self.roster)}")

    def write_meta(self) -> None:
        """Write metadata about the resume tailoring process."""
        directory = self.env_dict['directory']
        
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"{directory} Created.")

        meta_filename = "meta.txt"
        with open(os.path.join(directory, meta_filename), "w", encoding="utf-8") as writer:
            writer.write(f"Resume Content Length: {len(self.env_dict['resume_content'])} characters\n\n")
            writer.write(f"Job Description Length: {len(self.env_dict['job_description'])} characters\n\n")
            writer.write(f"Config:\n{self.config.__str__()}\n\n")
            writer.write(f"Roster: {', '.join(self.roster)}\n\n")
        print(f"{os.path.join(directory, meta_filename)} Written")