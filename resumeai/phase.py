# resumeai/phase.py
import os
import re
from abc import ABC, abstractmethod

from camel.agents import RolePlaying
from camel.messages import ChatMessage
from camel.typing import TaskType, ModelType
from resumeai.resume_env import ResumeEnv
from resumeai.utils import log_visualize

class Phase(ABC):
    """
    Abstract base class for all resume tailoring phases.
    Each phase represents a specific step in the resume tailoring process.
    """
    def __init__(self,
                 assistant_role_name,
                 user_role_name,
                 phase_prompt,
                 role_prompts,
                 phase_name,
                 model_type,
                 log_filepath):
        """
        Initialize a phase for resume tailoring.
        
        Args:
            assistant_role_name: Role that receives chat in this phase
            user_role_name: Role that starts the chat in this phase
            phase_prompt: Prompt template for this phase
            role_prompts: Dictionary of prompts for all roles
            phase_name: Name of this phase
            model_type: Language model to use
            log_filepath: Path to log file
        """
        self.seminar_conclusion = None
        self.assistant_role_name = assistant_role_name
        self.user_role_name = user_role_name
        self.phase_prompt = phase_prompt
        self.phase_env = dict()
        self.phase_name = phase_name
        self.assistant_role_prompt = role_prompts[assistant_role_name]
        self.user_role_prompt = role_prompts[user_role_name]
        self.model_type = model_type
        self.log_filepath = log_filepath
        self.max_retries = 3

    def chatting(self,
                resume_env,
                task_prompt: str,
                assistant_role_name: str,
                user_role_name: str,
                phase_prompt: str,
                phase_name: str,
                assistant_role_prompt: str,
                user_role_prompt: str,
                task_type=TaskType.CHATDEV,
                need_reflect=False,
                with_task_specify=False,
                model_type=ModelType.GPT_4O,
                memory=None,
                placeholders=None,
                chat_turn_limit=10) -> str:
        """
        Conduct a conversation between two agents to complete a phase.
        
        Args:
            resume_env: Global resume environment
            task_prompt: User query prompt for tailoring the resume
            assistant_role_name: Role that receives the chat
            user_role_name: Role that starts the chat
            phase_prompt: Prompt template for this phase
            phase_name: Name of this phase
            assistant_role_prompt: Prompt for assistant role
            user_role_prompt: Prompt for user role
            task_type: Type of task
            need_reflect: Whether to reflect on the conversation
            with_task_specify: Whether to use task specification
            model_type: Language model to use
            memory: Agent memory
            placeholders: Values to fill placeholders in phase prompt
            chat_turn_limit: Maximum number of turns in the chat
            
        Returns:
            seminar_conclusion: Conclusion of the conversation
        """
        if placeholders is None:
            placeholders = {}
        assert 1 <= chat_turn_limit <= 100

        if not resume_env.exist_employee(assistant_role_name):
            raise ValueError(f"{assistant_role_name} not recruited in ResumeEnv.")
        if not resume_env.exist_employee(user_role_name):
            raise ValueError(f"{user_role_name} not recruited in ResumeEnv.")

        # Initialize role play
        role_play_session = RolePlaying(
            assistant_role_name=assistant_role_name,
            user_role_name=user_role_name,
            assistant_role_prompt=assistant_role_prompt,
            user_role_prompt=user_role_prompt,
            task_prompt=task_prompt,
            task_type=task_type,
            with_task_specify=with_task_specify,
            memory=memory,
            model_type=model_type,
            background_prompt=resume_env.config.background_prompt
        )

        # Start the chat
        _, input_user_msg = role_play_session.init_chat(None, placeholders, phase_prompt)
        seminar_conclusion = None

        # Handle chats
        for i in range(chat_turn_limit):
            assistant_response, user_response = role_play_session.step(input_user_msg, chat_turn_limit == 1)

            conversation_meta = f"**{assistant_role_name}<->{user_role_name} on : {phase_name}, turn {i}**\n\n"

            if isinstance(assistant_response.msg, ChatMessage):
                log_visualize(role_play_session.assistant_agent.role_name,
                             conversation_meta + "[" + role_play_session.user_agent.system_message.content + "]\n\n" + assistant_response.msg.content)
                if role_play_session.assistant_agent.info:
                    seminar_conclusion = assistant_response.msg.content
                    break
                if assistant_response.terminated:
                    break

            if isinstance(user_response.msg, ChatMessage):
                log_visualize(role_play_session.user_agent.role_name,
                             conversation_meta + "[" + role_play_session.assistant_agent.system_message.content + "]\n\n" + user_response.msg.content)
                if role_play_session.user_agent.info:
                    seminar_conclusion = user_response.msg.content
                    break
                if user_response.terminated:
                    break

            # Continue the chat
            if chat_turn_limit > 1 and isinstance(user_response.msg, ChatMessage):
                input_user_msg = user_response.msg
            else:
                break

        seminar_conclusion = seminar_conclusion or assistant_response.msg.content
        log_visualize(f"**[Seminar Conclusion]**:\n\n{seminar_conclusion}")
        
        return seminar_conclusion

    @abstractmethod
    def update_phase_env(self, resume_env):
        """
        Update phase-specific environment variables from the global environment.
        Must be implemented in each phase subclass.
        
        Args:
            resume_env: Global resume environment
        """
        pass

    @abstractmethod
    def update_resume_env(self, resume_env) -> ResumeEnv:
        """
        Update global environment based on the results of this phase.
        Must be implemented in each phase subclass.
        
        Args:
            resume_env: Global resume environment
            
        Returns:
            Updated global resume environment
        """
        pass

    def execute(self, resume_env, chat_turn_limit, need_reflect) -> ResumeEnv:
        """
        Execute the chatting in this phase.
        
        Args:
            resume_env: Global resume environment
            chat_turn_limit: Maximum number of turns in the chat
            need_reflect: Whether to reflect on the conversation
            
        Returns:
            Updated global resume environment
        """
        self.update_phase_env(resume_env)
        self.seminar_conclusion = \
            self.chatting(resume_env=resume_env,
                          task_prompt="Tailor a resume for a specific job description",
                          need_reflect=need_reflect,
                          assistant_role_name=self.assistant_role_name,
                          user_role_name=self.user_role_name,
                          phase_prompt=self.phase_prompt,
                          phase_name=self.phase_name,
                          assistant_role_prompt=self.assistant_role_prompt,
                          user_role_prompt=self.user_role_prompt,
                          chat_turn_limit=chat_turn_limit,
                          placeholders=self.phase_env,
                          memory=resume_env.memory,
                          model_type=self.model_type)
        resume_env = self.update_resume_env(resume_env)
        return resume_env


class ResumeAnalysis(Phase):
    """Phase for analyzing the structure and content of the resume."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "resume_content": resume_env.env_dict['resume_content']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        # Extract work experience and skills sections from the resume
        sections = {}
        text = resume_env.env_dict['resume_content']
        
        # Find work experience section
        work_exp_match = re.search(r'\\section\{(Work\s*Experience|Professional\s*Experience|Employment)[^\}]*\}(.*?)(?=\\section\{|$)', text, re.DOTALL)
        if work_exp_match:
            sections['work_experience'] = work_exp_match.group(2).strip()
        
        # Find skills section
        skills_match = re.search(r'\\section\{(Skills|Technical\s*Skills)[^\}]*\}(.*?)(?=\\section\{|$)', text, re.DOTALL)
        if skills_match:
            sections['skills'] = skills_match.group(2).strip()
        
        # Store in the environment
        resume_env.env_dict['resume_work_experience'] = sections.get('work_experience', '')
        resume_env.env_dict['resume_skills'] = sections.get('skills', '')
        resume_env.env_dict['original_resume'] = resume_env.env_dict['resume_content']
        
        return resume_env


class JobDescriptionAnalysis(Phase):
    """Phase for analyzing the job description to extract key requirements."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "job_description": resume_env.env_dict['job_description']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        resume_env.env_dict['job_description_analysis'] = self.seminar_conclusion
        return resume_env


class WorkExperienceUpdate(Phase):
    """Phase for updating the work experience section based on job requirements."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "resume_work_experience": resume_env.env_dict['resume_work_experience'],
            "job_description_analysis": resume_env.env_dict['job_description_analysis']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        resume_env.env_dict['updated_work_experience'] = self.seminar_conclusion
        return resume_env


class SkillsUpdate(Phase):
    """Phase for updating the skills section based on job requirements."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "resume_skills": resume_env.env_dict['resume_skills'],
            "job_description_analysis": resume_env.env_dict['job_description_analysis']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        resume_env.env_dict['updated_skills'] = self.seminar_conclusion
        return resume_env


class QualityReviewComment(Phase):
    """Phase for reviewing the updated resume sections."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "updated_work_experience": resume_env.env_dict['updated_work_experience'],
            "updated_skills": resume_env.env_dict['updated_skills']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        resume_env.env_dict['quality_feedback'] = self.seminar_conclusion
        return resume_env


class QualityRevision(Phase):
    """Phase for revising the resume based on quality feedback."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "quality_feedback": resume_env.env_dict['quality_feedback'],
            "updated_work_experience": resume_env.env_dict['updated_work_experience'],
            "updated_skills": resume_env.env_dict['updated_skills']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        # Parse the response to update both work experience and skills sections
        result = self.seminar_conclusion
        
        work_exp_pattern = r'Work Experience:(.*?)(?=Skills:|$)'
        skills_pattern = r'Skills:(.*)'
        
        work_exp_match = re.search(work_exp_pattern, result, re.DOTALL)
        skills_match = re.search(skills_pattern, result, re.DOTALL)
        
        if work_exp_match:
            resume_env.env_dict['updated_work_experience'] = work_exp_match.group(1).strip()
        
        if skills_match:
            resume_env.env_dict['updated_skills'] = skills_match.group(1).strip()
        
        return resume_env


class SummaryWriting(Phase):
    """Phase for writing a professional summary based on updated resume sections."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "updated_work_experience": resume_env.env_dict['updated_work_experience'],
            "updated_skills": resume_env.env_dict['updated_skills'],
            "job_description_analysis": resume_env.env_dict['job_description_analysis']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        resume_env.env_dict['updated_summary'] = self.seminar_conclusion
        return resume_env


class ResumeAssembly(Phase):
    """Phase for assembling the final resume with updated sections."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "original_resume": resume_env.env_dict['original_resume'],
            "updated_summary": resume_env.env_dict['updated_summary'],
            "updated_skills": resume_env.env_dict['updated_skills'],
            "updated_work_experience": resume_env.env_dict['updated_work_experience']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        resume_env.env_dict['final_resume'] = self.seminar_conclusion
        
        # Save the final resume
        if resume_env.config.latex_output:
            output_path = os.path.join(resume_env.env_dict['directory'], "tailored_resume.tex")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(self.seminar_conclusion)
            print(f"Tailored resume saved to {output_path}")
        
        return resume_env


class FinalReview(Phase):
    """Phase for providing a final review of the tailored resume."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, resume_env):
        self.phase_env.update({
            "final_resume": resume_env.env_dict['final_resume'],
            "original_resume": resume_env.env_dict['original_resume'],
            "job_description": resume_env.env_dict['job_description']
        })

    def update_resume_env(self, resume_env) -> ResumeEnv:
        # Save the review
        output_path = os.path.join(resume_env.env_dict['directory'], "review_summary.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.seminar_conclusion)
        print(f"Review summary saved to {output_path}")
        
        return resume_env