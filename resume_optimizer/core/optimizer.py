"""Main resume optimizer module."""

from resume_optimizer.core.job_analyzer import JobAnalyzer
from resume_optimizer.agents.skill_agent import SkillOptimizerAgent
from resume_optimizer.agents.experience_agent import ExperienceOptimizerAgent
from resume_optimizer.agents.evaluator_agent import EvaluatorAgent
from resume_optimizer.agents.ats_agent import ATSCompatibilityAgent
from resume_optimizer.utils.latex_utils import (
    read_latex_file, 
    save_latex_file, 
    extract_section, 
    replace_section
)


class ResumeOptimizer:
    """Main class that orchestrates the resume optimization process."""
    
    def __init__(self, resume_path, job_description, output_path="optimized_resume.tex", model=None):
        """Initialize the resume optimizer.
        
        Args:
            resume_path: Path to the LaTeX resume file
            job_description: Job description text
            output_path: Path where the optimized resume will be saved
            model: Optional model to use for agents
        """
        self.resume_path = resume_path
        self.job_description = job_description
        self.output_path = output_path
        self.resume_content = read_latex_file(resume_path)
        self.model = model
        
        # Initialize agents
        self.job_analyzer = JobAnalyzer(model=model)
        self.skill_agent = SkillOptimizerAgent(model=model)
        self.experience_agent = ExperienceOptimizerAgent(model=model)
        self.evaluator = EvaluatorAgent(model=model)
        self.ats_agent = ATSCompatibilityAgent(model=model)
    
    def run(self):
        """Run the full resume optimization pipeline with iterative improvement.
        
        Returns:
            The optimized resume content as a string
        """
        print("🚀 Starting Resume Optimization")
        
        # Step 1: Analyze job description
        print("\n🔄 Analyzing job description...")
        jd_analysis = self.job_analyzer.optimize(self.job_description)
        
        # Extract sections
        skills_section = extract_section(self.resume_content, "TECHNICAL SKILLS")
        experience_section = extract_section(self.resume_content, "EXPERIENCE")
        
        # First cycle optimization
        print("\n🔄 First pass: Optimizing technical skills section...")
        optimized_skills = self.skill_agent.optimize(skills_section, jd_analysis)
        
        print("\n🔄 First pass: Optimizing work experience section...")
        optimized_experience = self.experience_agent.optimize(experience_section, jd_analysis)
        
        # Evaluation
        print("\n🔄 Evaluating optimizations...")
        skills_feedback = self.evaluator.evaluate_section(
            "skills", skills_section, optimized_skills, jd_analysis
        )
        experience_feedback = self.evaluator.evaluate_section(
            "experience", experience_section, optimized_experience, jd_analysis
        )
        
        # Second cycle optimization with feedback
        print("\n🔄 Second pass: Re-optimizing technical skills with feedback...")
        final_skills = self.skill_agent.refine_with_feedback(
            optimized_skills, skills_feedback, jd_analysis
        )
        
        print("\n🔄 Second pass: Re-optimizing work experience with feedback...")
        final_experience = self.experience_agent.refine_with_feedback(
            optimized_experience, experience_feedback, jd_analysis
        )
        
        # Update the resume content
        updated_resume = self.resume_content
        updated_resume = replace_section(updated_resume, "TECHNICAL SKILLS", final_skills)
        updated_resume = replace_section(updated_resume, "EXPERIENCE", final_experience)
        
        # Check ATS compatibility
        print("\n🔄 Checking ATS compatibility...")
        ats_score, ats_feedback = self.ats_agent.check_compatibility(
            updated_resume, self.job_description
        )
        print(f"\n✅ ATS Check Complete - Score: {ats_score}/100")
        print(f"ATS Feedback: {ats_feedback}")
        
        # Save the optimized resume
        save_latex_file(updated_resume, self.output_path)
        print(f"\n✅ Optimized resume saved to {self.output_path}")
        
        return updated_resume
    
    def validate_latex_formatting(self, skills_section, experience_section):
        """Validate and fix LaTeX formatting in optimized sections.
        
        This method is a placeholder for future implementation of LaTeX validation.
        It would ensure that the generated LaTeX is valid and properly formatted.
        
        Args:
            skills_section: The skills section content
            experience_section: The experience section content
            
        Returns:
            Tuple of (validated_skills, validated_experience)
        """
        # This could be implemented to check for LaTeX syntax errors, proper nesting, etc.
        # For now, we'll just return the input sections
        return skills_section, experience_section