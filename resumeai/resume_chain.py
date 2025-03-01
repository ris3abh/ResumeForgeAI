# resumeai/resume_chain.py
import importlib
import json
import logging
import os
import shutil
import time
from datetime import datetime

from camel.agents import RolePlaying
from camel.configs import ChatGPTConfig
from camel.typing import TaskType, ModelType
from resumeai.resume_env import ResumeEnv, ResumeEnvConfig
from resumeai.statistics import get_info
from resumeai.utils import log_visualize, now


def check_bool(s):
    return s.lower() == "true"


class ResumeChain:
    def __init__(self,
                 config_path: str = None,
                 config_phase_path: str = None,
                 config_role_path: str = None,
                 resume_content: str = None,
                 job_description: str = None,
                 project_name: str = None,
                 org_name: str = None,
                 model_type: ModelType = ModelType.GPT_4O,
                 output_dir: str = "Outputs") -> None:
        """
        Initialize the ResumeChain for the resume tailoring process.

        Args:
            config_path: path to the ChatChainConfig.json
            config_phase_path: path to the PhaseConfig.json
            config_role_path: path to the RoleConfig.json
            resume_content: content of the LaTeX resume
            job_description: content of the job description
            project_name: name for the output files
            org_name: organization name
            model_type: OpenAI model to use
            output_dir: directory for output files
        """
        # Load config files
        self.config_path = config_path
        self.config_phase_path = config_phase_path
        self.config_role_path = config_role_path
        self.resume_content = resume_content
        self.job_description = job_description
        self.project_name = project_name
        self.org_name = org_name
        self.model_type = model_type
        self.output_dir = output_dir

        with open(self.config_path, 'r', encoding="utf8") as file:
            self.config = json.load(file)
        with open(self.config_phase_path, 'r', encoding="utf8") as file:
            self.config_phase = json.load(file)
        with open(self.config_role_path, 'r', encoding="utf8") as file:
            self.config_role = json.load(file)

        # Initialize chain config and recruitments
        self.chain = self.config["chain"]
        self.recruitments = self.config["recruitments"]
        
        # Initialize default max chat turn
        self.chat_turn_limit_default = 10

        # Initialize ResumeEnv
        self.resume_env_config = ResumeEnvConfig(
            latex_output=check_bool(self.config.get("latex_output", "True")),
            clear_structure=check_bool(self.config.get("clear_structure", "True")),
            with_memory=check_bool(self.config.get("with_memory", "True")),
            background_prompt=self.config.get("background_prompt", "")
        )
        
        self.resume_env = ResumeEnv(self.resume_env_config)
        
        # Initialize role prompts
        self.role_prompts = dict()
        for role in self.config_role:
            self.role_prompts[role] = "\n".join(self.config_role[role])

        # Initialize log
        self.start_time, self.log_filepath = self.get_logfilepath()
        
        # Import phase modules
        self.compose_phase_module = importlib.import_module("resumeai.composed_phase")
        self.phase_module = importlib.import_module("resumeai.phase")
        
        # Initialize phases
        self.phases = dict()
        for phase in self.config_phase:
            assistant_role_name = self.config_phase[phase]['assistant_role_name']
            user_role_name = self.config_phase[phase]['user_role_name']
            phase_prompt = "\n\n".join(self.config_phase[phase]['phase_prompt'])
            phase_class = getattr(self.phase_module, phase)
            phase_instance = phase_class(
                assistant_role_name=assistant_role_name,
                user_role_name=user_role_name,
                phase_prompt=phase_prompt,
                role_prompts=self.role_prompts,
                phase_name=phase,
                model_type=self.model_type,
                log_filepath=self.log_filepath
            )
            self.phases[phase] = phase_instance

    def make_recruitment(self):
        """
        Recruit all agents specified in the configuration.
        """
        for agent in self.recruitments:
            self.resume_env.recruit(agent_name=agent)

    def execute_step(self, phase_item: dict):
        """
        Execute a single phase in the chain.
        
        Args:
            phase_item: Single phase configuration from ChatChainConfig.json
        """
        phase = phase_item['phase']
        phase_type = phase_item['phaseType']
        
        # For SimplePhase, look it up from self.phases and execute it
        if phase_type == "SimplePhase":
            max_turn_step = phase_item['max_turn_step']
            need_reflect = check_bool(phase_item['need_reflect'])
            
            if phase in self.phases:
                self.resume_env = self.phases[phase].execute(
                    self.resume_env,
                    self.chat_turn_limit_default if max_turn_step <= 0 else max_turn_step,
                    need_reflect
                )
            else:
                raise RuntimeError(f"Phase '{phase}' is not yet implemented in resumeai.phase")
        
        # For ComposedPhase, create an instance and execute it
        elif phase_type == "ComposedPhase":
            cycle_num = phase_item['cycleNum']
            composition = phase_item['Composition']
            compose_phase_class = getattr(self.compose_phase_module, phase)
            
            if not compose_phase_class:
                raise RuntimeError(f"Phase '{phase}' is not yet implemented in resumeai.composed_phase")
                
            compose_phase_instance = compose_phase_class(
                phase_name=phase,
                cycle_num=cycle_num,
                composition=composition,
                config_phase=self.config_phase,
                config_role=self.config_role,
                model_type=self.model_type,
                log_filepath=self.log_filepath
            )
            
            self.resume_env = compose_phase_instance.execute(self.resume_env)
        else:
            raise RuntimeError(f"PhaseType '{phase_type}' is not yet implemented.")

    def execute_chain(self):
        """
        Execute the entire chain defined in ChatChainConfig.json.
        """
        for phase_item in self.chain:
            self.execute_step(phase_item)

    def get_logfilepath(self):
        """
        Get the log file path.
        
        Returns:
            start_time: Time when the process started
            log_filepath: Path to the log file
        """
        start_time = now()
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)
        
        # Create output directory if it doesn't exist
        directory = os.path.join(root, self.output_dir)
        os.makedirs(directory, exist_ok=True)
        
        log_filepath = os.path.join(
            directory,
            "{}.log".format("_".join([self.project_name, self.org_name, start_time]))
        )
        
        return start_time, log_filepath

    def pre_processing(self):
        """
        Prepare the environment before executing the chain.
        """
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)
        directory = os.path.join(root, self.output_dir)
        
        # Clean up old files if clear_structure is enabled
        if self.resume_env.config.clear_structure:
            # Only delete non-essential files in the output directory
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path) and not filename.endswith(".tex") and not filename.endswith(".log"):
                    os.remove(file_path)
                    print(f"{file_path} Removed.")
        
        # Set up output directory
        output_path = os.path.join(directory, "_".join([self.project_name, self.org_name, self.start_time]))
        self.resume_env.set_directory(output_path)
        
        # Initialize memory if enabled
        if self.resume_env.config.with_memory:
            self.resume_env.init_memory()
        
        # Copy config files to output path
        os.makedirs(output_path, exist_ok=True)
        shutil.copy(self.config_path, output_path)
        shutil.copy(self.config_phase_path, output_path)
        shutil.copy(self.config_role_path, output_path)
        
        # Save original resume and job description
        with open(os.path.join(output_path, "original_resume.tex"), "w") as f:
            f.write(self.resume_content)
        with open(os.path.join(output_path, "job_description.txt"), "w") as f:
            f.write(self.job_description)
        
        # Log preprocessing information
        preprocess_msg = "**[Preprocessing]**\n\n"
        chat_gpt_config = ChatGPTConfig()
        
        preprocess_msg += f"**ResumeAI Starts** ({self.start_time})\n\n"
        preprocess_msg += f"**Timestamp**: {self.start_time}\n\n"
        preprocess_msg += f"**config_path**: {self.config_path}\n\n"
        preprocess_msg += f"**config_phase_path**: {self.config_phase_path}\n\n"
        preprocess_msg += f"**config_role_path**: {self.config_role_path}\n\n"
        preprocess_msg += f"**resume_length**: {len(self.resume_content)} characters\n\n"
        preprocess_msg += f"**job_description_length**: {len(self.job_description)} characters\n\n"
        preprocess_msg += f"**project_name**: {self.project_name}\n\n"
        preprocess_msg += f"**Log File**: {self.log_filepath}\n\n"
        preprocess_msg += f"**ResumeEnvConfig**:\n{self.resume_env.config.__str__()}\n\n"
        preprocess_msg += f"**ChatGPTConfig**:\n{chat_gpt_config}\n\n"
        
        log_visualize(preprocess_msg)
        
        # Initialize environment variables
        self.resume_env.env_dict['resume_content'] = self.resume_content
        self.resume_env.env_dict['job_description'] = self.job_description

    def post_processing(self):
        """
        Finalize the process after execution.
        """
        self.resume_env.write_meta()
        filepath = os.path.dirname(__file__)
        root = os.path.dirname(filepath)
        
        # Calculate process duration
        now_time = now()
        time_format = "%Y%m%d%H%M%S"
        datetime1 = datetime.strptime(self.start_time, time_format)
        datetime2 = datetime.strptime(now_time, time_format)
        duration = (datetime2 - datetime1).total_seconds()
        
        # Generate post-processing information
        post_info = "**[Post Info]**\n\n"
        post_info += f"Resume Info: {get_info(self.resume_env.env_dict['directory'], self.log_filepath)}\n\n"
        post_info += f"🕑**duration**={duration:.2f}s\n\n"
        post_info += f"ResumeAI Starts ({self.start_time})\n\n"
        post_info += f"ResumeAI Ends ({now_time})\n\n"
        
        # Clean up temporary files if needed
        directory = self.resume_env.env_dict['directory']
        if self.resume_env.config.clear_structure:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isdir(file_path) and file_path.endswith("__pycache__"):
                    shutil.rmtree(file_path, ignore_errors=True)
                    post_info += f"{file_path} Removed.\n\n"
        
        log_visualize(post_info)
        
        # Shutdown logging and move log file
        logging.shutdown()
        time.sleep(1)
        
        output_dir_path = os.path.join(root, self.output_dir)
        result_dir = os.path.join(output_dir_path, "_".join([self.project_name, self.org_name, self.start_time]))
        
        try:
            shutil.move(
                self.log_filepath,
                os.path.join(result_dir, os.path.basename(self.log_filepath))
            )
        except Exception as e:
            print(f"Warning: Could not move log file: {e}")