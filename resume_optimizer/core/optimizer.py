"""Main resume optimizer module."""

import os
from colorama import Fore, Style

from resume_optimizer.core.job_analyzer import JobAnalyzer
from resume_optimizer.agents.skill_agent import SkillOptimizerAgent
from resume_optimizer.agents.experience_agent import ExperienceOptimizerAgent
from resume_optimizer.agents.evaluator_agent import EvaluatorAgent
from resume_optimizer.agents.ats_agent import ATSCompatibilityAgent
from resume_optimizer.core.latex_handler import LatexHandler
from resume_optimizer.utils.latex_utils import (
    read_latex_file, 
    save_latex_file, 
    extract_section, 
    replace_section
)


class ResumeOptimizer:
    """Main class that orchestrates the resume optimization process."""
    
    def __init__(self, resume_path, job_description, output_path="optimized_resume.tex", model=None, debug_mode=True):
        """Initialize the resume optimizer.
        
        Args:
            resume_path: Path to the LaTeX resume file
            job_description: Job description text
            output_path: Path where the optimized resume will be saved
            model: Optional model to use for agents
            debug_mode: Whether to print debug information
        """
        self.resume_path = resume_path
        self.job_description = job_description
        self.output_path = output_path
        self.model = model
        self.debug_mode = debug_mode
        
        # Initialize the latex handler
        self.latex_handler = LatexHandler(debug_mode=debug_mode)
        self.resume_content = self.latex_handler.read_resume(resume_path)
        
        # Initialize agents
        self.job_analyzer = JobAnalyzer(model=model)
        self.skill_agent = SkillOptimizerAgent(model=model)
        self.experience_agent = ExperienceOptimizerAgent(model=model)
        self.evaluator = EvaluatorAgent(model=model)
        self.ats_agent = ATSCompatibilityAgent(model=model)
        
        # Create debug directory if needed
        if self.debug_mode:
            os.makedirs("debug_output", exist_ok=True)
    
    def run(self):
        """Run the full resume optimization pipeline with iterative improvement.
        
        Returns:
            The optimized resume content as a string
        """
        print(f"{Fore.YELLOW}🚀 Starting Resume Optimization{Style.RESET_ALL}")
        
        # Step 1: Analyze job description
        print(f"\n{Fore.CYAN}🔄 Analyzing job description...{Style.RESET_ALL}")
        jd_analysis = self.job_analyzer.optimize(self.job_description)
        
        # Save job analysis for debugging
        if self.debug_mode:
            with open("debug_output/job_analysis.txt", "w") as f:
                f.write(str(jd_analysis))
        
        # Extract sections
        skills_section = extract_section(self.resume_content, "TECHNICAL SKILLS")
        experience_section = extract_section(self.resume_content, "EXPERIENCE")
        
        # Log the job analysis and section extraction
        self.latex_handler.log_agent_communication(
            agent_name="Job Analyzer",
            input_data=self.job_description,
            output_data=str(jd_analysis),
            context={"step": "Initial Job Analysis"}
        )
        
        # First cycle optimization
        print(f"\n{Fore.CYAN}🔄 First pass: Optimizing technical skills section...{Style.RESET_ALL}")
        optimized_skills = self.skill_agent.optimize(skills_section, jd_analysis)
        
        # Log the skills optimization
        self.latex_handler.log_optimization_result(
            section_name="TECHNICAL SKILLS",
            original=skills_section,
            optimized=optimized_skills,
            analysis_results=jd_analysis
        )
        
        # For debugging, write to files
        if self.debug_mode:
            with open("debug_output/original_skills.tex", "w") as f:
                f.write(skills_section)
            with open("debug_output/optimized_skills_first_pass.tex", "w") as f:
                f.write(optimized_skills)
        
        print(f"\n{Fore.CYAN}🔄 First pass: Optimizing work experience section...{Style.RESET_ALL}")
        optimized_experience = self.experience_agent.optimize(experience_section, jd_analysis)
        
        # Log the experience optimization
        self.latex_handler.log_optimization_result(
            section_name="EXPERIENCE",
            original=experience_section,
            optimized=optimized_experience,
            analysis_results=jd_analysis
        )
        
        # For debugging, write to files
        if self.debug_mode:
            with open("debug_output/original_experience.tex", "w") as f:
                f.write(experience_section)
            with open("debug_output/optimized_experience_first_pass.tex", "w") as f:
                f.write(optimized_experience)
        
        # Create intermediate resume for evaluation
        intermediate_resume = self.resume_content
        intermediate_resume = replace_section(intermediate_resume, "TECHNICAL SKILLS", optimized_skills)
        intermediate_resume = replace_section(intermediate_resume, "EXPERIENCE", optimized_experience)
        
        if self.debug_mode:
            with open("debug_output/intermediate_resume.tex", "w") as f:
                f.write(intermediate_resume)
        
        # Evaluation
        print(f"\n{Fore.CYAN}🔄 Evaluating optimizations...{Style.RESET_ALL}")
        skills_feedback = self.evaluator.evaluate_section(
            "skills", skills_section, optimized_skills, jd_analysis
        )
        experience_feedback = self.evaluator.evaluate_section(
            "experience", experience_section, optimized_experience, jd_analysis
        )
        
        # Log the evaluation feedback
        if self.debug_mode:
            with open("debug_output/skills_feedback.txt", "w") as f:
                f.write(skills_feedback)
            with open("debug_output/experience_feedback.txt", "w") as f:
                f.write(experience_feedback)
        
        # Second cycle optimization with feedback
        print(f"\n{Fore.CYAN}🔄 Second pass: Re-optimizing technical skills with feedback...{Style.RESET_ALL}")
        final_skills = self.skill_agent.refine_with_feedback(
            optimized_skills, skills_feedback, jd_analysis
        )
        
        # Log the refined skills optimization
        self.latex_handler.log_optimization_result(
            section_name="TECHNICAL SKILLS (Refined)",
            original=optimized_skills,
            optimized=final_skills,
            analysis_results=jd_analysis
        )
        
        if self.debug_mode:
            with open("debug_output/optimized_skills_second_pass.tex", "w") as f:
                f.write(final_skills)
        
        print(f"\n{Fore.CYAN}🔄 Second pass: Re-optimizing work experience with feedback...{Style.RESET_ALL}")
        final_experience = self.experience_agent.refine_with_feedback(
            optimized_experience, experience_feedback, jd_analysis
        )
        
        # Log the refined experience optimization
        self.latex_handler.log_optimization_result(
            section_name="EXPERIENCE (Refined)",
            original=optimized_experience,
            optimized=final_experience,
            analysis_results=jd_analysis
        )
        
        if self.debug_mode:
            with open("debug_output/optimized_experience_second_pass.tex", "w") as f:
                f.write(final_experience)
        
        # Update the resume content
        updated_resume = self.resume_content
        updated_resume = replace_section(updated_resume, "TECHNICAL SKILLS", final_skills)
        updated_resume = replace_section(updated_resume, "EXPERIENCE", final_experience)
        
        # Check ATS compatibility
        print(f"\n{Fore.CYAN}🔄 Checking ATS compatibility...{Style.RESET_ALL}")
        ats_score, ats_feedback = self.ats_agent.check_compatibility(
            updated_resume, self.job_description
        )
        print(f"\n{Fore.GREEN}✅ ATS Check Complete - Score: {ats_score}/100{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}ATS Feedback:{Style.RESET_ALL} {ats_feedback}")
        
        if self.debug_mode:
            with open("debug_output/ats_feedback.txt", "w") as f:
                f.write(f"Score: {ats_score}/100\n\n{ats_feedback}")
        
        # Save the optimized resume
        self.latex_handler.save_resume(updated_resume, self.output_path)
        print(f"\n{Fore.GREEN}✅ Optimized resume saved to {self.output_path}{Style.RESET_ALL}")
        
        # If debug mode, generate a comparison
        if self.debug_mode:
            print(f"\n{Fore.CYAN}🔄 Generating resume comparison...{Style.RESET_ALL}")
            self.latex_handler.compare_resumes(self.resume_path, self.output_path)
            print(f"{Fore.GREEN}✅ Resume comparison complete. See log for details.{Style.RESET_ALL}")
        
        return updated_resume
    
    def validate_latex_formatting(self, skills_section, experience_section):
        """Validate and fix LaTeX formatting in optimized sections.
        
        This method ensures that the generated LaTeX is valid and properly formatted.
        
        Args:
            skills_section: The skills section content
            experience_section: The experience section content
            
        Returns:
            Tuple of (validated_skills, validated_experience)
        """
        # Check for common LaTeX errors
        def validate_section(section, section_name):
            # Ensure proper nesting of environments
            if section.count("\\resumeSubHeadingListStart") != section.count("\\resumeSubHeadingListEnd"):
                print(f"{Fore.RED}Warning: Mismatched \\resumeSubHeadingListStart and \\resumeSubHeadingListEnd in {section_name}{Style.RESET_ALL}")
                # Try to fix
                if section.count("\\resumeSubHeadingListStart") > section.count("\\resumeSubHeadingListEnd"):
                    section += "\n\\resumeSubHeadingListEnd"
                else:
                    section = "\\resumeSubHeadingListStart\n" + section
            
            # Ensure proper nesting of item environments
            if section.count("\\resumeItemListStart") != section.count("\\resumeItemListEnd"):
                print(f"{Fore.RED}Warning: Mismatched \\resumeItemListStart and \\resumeItemListEnd in {section_name}{Style.RESET_ALL}")
                # Fix would depend on the specific structure, just log for now
            
            return section
        
        validated_skills = validate_section(skills_section, "skills")
        validated_experience = validate_section(experience_section, "experience")
        
        return validated_skills, validated_experience