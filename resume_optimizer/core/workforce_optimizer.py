"""ResumeForgeAI: CAMEL Workforce-powered resume optimizer."""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from colorama import Fore, Style, init

# Initialize colorama
init()

from camel.societies.workforce import Workforce
from camel.tasks import Task
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.types import RoleType, ModelType

from resume_optimizer.agents.experience_agent import ExperienceOptimizerAgent
from resume_optimizer.agents.skill_agent import SkillOptimizerAgent
from resume_optimizer.agents.ats_agent import ATSCompatibilityAgent
from resume_optimizer.agents.evaluator_agent import EvaluatorAgent
from resume_optimizer.core.job_analyzer import JobAnalyzer
from resume_optimizer.core.latex_handler import LatexHandler
from resume_optimizer.utils.model_factory import create_default_model, get_model_by_name
from resume_optimizer.utils.latex_utils import extract_section, extract_latex_content

logger = logging.getLogger(__name__)

class WorkforceResumeOptimizer:
    """CAMEL Workforce-powered resume optimizer with enhanced capabilities."""
    
    def __init__(
        self, 
        resume_path: str, 
        job_description: str, 
        output_path: str = "optimized_resume.tex", 
        model: Any = None, 
        debug_mode: bool = True,
        verbose: bool = True,
        sections_to_optimize: Optional[List[str]] = None,
        optimization_iterations: int = 2
    ):
        """Initialize the workforce resume optimizer.
        
        Args:
            resume_path: Path to the LaTeX resume file
            job_description: Job description text
            output_path: Path where the optimized resume will be saved
            model: Optional model to use for agents
            debug_mode: Whether to save debug information and files
            verbose: Whether to print detailed output
            sections_to_optimize: List of specific sections to optimize (default: all relevant sections)
            optimization_iterations: Number of optimization iterations to perform
        """
        self.resume_path = resume_path
        self.job_description = job_description
        self.output_path = output_path
        self.model = model if model else create_default_model()
        self.debug_mode = debug_mode
        self.verbose = verbose
        self.optimization_iterations = optimization_iterations
        
        # Default sections to optimize
        self.default_sections = [
            "PROFESSIONAL SUMMARY", 
            "TECHNICAL SKILLS", 
            "EXPERIENCE"
        ]
        
        self.sections_to_optimize = sections_to_optimize or self.default_sections
        
        # Initialize the LaTeX handler
        self.latex_handler = LatexHandler(debug_mode=debug_mode)
        
        # Initialize the workforce coordinator
        self.workforce = self._setup_workforce()
        
        # Create directories
        os.makedirs("debug_output", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Track metrics
        self.metrics = {
            "start_time": time.time(),
            "sections_optimized": 0,
            "optimization_metrics": {},
            "ats_scores": {
                "initial": 0,
                "final": 0
            }
        }
    
    def _setup_workforce(self) -> Workforce:
        """Set up the resume optimization workforce.
        
        Returns:
            Configured CAMEL Workforce
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Setting up Resume Optimization Workforce...{Style.RESET_ALL}")
        
        # Initialize the workforce
        workforce = Workforce("Resume Optimization Workforce")
        
        # Add job analyzer worker
        job_analyzer = JobAnalyzer(model=self.model, verbose=self.verbose)
        workforce.add_single_agent_worker(
            "Analyzes job descriptions to extract key requirements, skills, and keywords",
            worker=job_analyzer
        )
        
        # Add skills optimizer worker
        skills_optimizer = SkillOptimizerAgent(model=self.model, verbose=self.verbose)
        workforce.add_single_agent_worker(
            "Optimizes technical skills sections to match job requirements",
            worker=skills_optimizer
        )
        
        # Add experience optimizer worker
        experience_optimizer = ExperienceOptimizerAgent(model=self.model, verbose=self.verbose)
        workforce.add_single_agent_worker(
            "Enhances work experience sections to highlight relevant achievements",
            worker=experience_optimizer
        )
        
        # Add professional summary optimizer worker
        system_message = (
            "You are a master of Resume Customization and have a proven track record of getting calls from resumes. "
            "You specialize in optimizing professional summary sections to perfectly match job descriptions. "
            "You create concise, powerful summaries that highlight the candidate's alignment with job requirements "
            "while emphasizing their unique value proposition."
        )
        summary_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="Professional Summary Optimizer",
                content=system_message
            ),
            model=self.model
        )
        workforce.add_single_agent_worker(
            "Creates powerful professional summaries aligned with job requirements",
            worker=summary_agent
        )
        
        # Add evaluator worker
        evaluator = EvaluatorAgent(model=self.model, verbose=self.verbose)
        workforce.add_single_agent_worker(
            "Evaluates optimization results and provides feedback for improvement",
            worker=evaluator
        )
        
        # Add ATS compatibility checker worker
        ats_checker = ATSCompatibilityAgent(model=self.model, verbose=self.verbose)
        workforce.add_single_agent_worker(
            "Checks ATS compatibility of resumes against job descriptions",
            worker=ats_checker
        )
        
        # Add resume assembler worker
        system_message = (
            "You are an expert at assembling optimized resume sections into a complete, "
            "cohesive resume. You understand LaTeX formatting and ensure that all sections "
            "are properly integrated while maintaining consistent formatting and style."
        )
        assembler_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="Resume Assembler",
                content=system_message
            ),
            model=self.model
        )
        workforce.add_single_agent_worker(
            "Assembles optimized sections into a complete resume",
            worker=assembler_agent
        )
        
        if self.verbose:
            print(f"{Fore.GREEN}Workforce setup complete!{Style.RESET_ALL}")
        
        return workforce
    
    def _analyze_job_description(self) -> Dict[str, Any]:
        """Analyze the job description.
        
        Returns:
            Dictionary with job analysis results
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Analyzing job description...{Style.RESET_ALL}")
        
        # Create a job analysis task
        task = Task(
            content="Analyze job description to extract skills, requirements, and keywords",
            id="analyze_job",
        )
        task.job_description = self.job_description
        
        # Process the task using the workforce
        analyze_result = self.workforce.process_task(task)
        
        if self.verbose:
            print(f"{Fore.GREEN}Job description analysis complete!{Style.RESET_ALL}")
        
        return analyze_result.result
    
    def _extract_resume_sections(self) -> Dict[str, str]:
        """Extract sections from the resume.
        
        Returns:
            Dictionary mapping section names to their content
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Extracting resume sections...{Style.RESET_ALL}")
            
        # Read the resume
        resume_content = self.latex_handler.read_resume(self.resume_path)
        
        # Extract sections
        sections = self.latex_handler.extract_sections(resume_content)
        
        if self.verbose:
            print(f"{Fore.GREEN}Extracted {len(sections)} sections from resume{Style.RESET_ALL}")
            
        return sections
    
    def _optimize_section(self, section_name: str, section_content: str, 
                      analysis_results: Dict[str, Any], iteration: int = 1) -> Tuple[str, Dict[str, Any]]:
        """Optimize a resume section.
        
        Args:
            section_name: Name of the section to optimize
            section_content: Content of the section
            analysis_results: Job description analysis results
            iteration: Current optimization iteration
            
        Returns:
            Tuple of (optimized content, optimization metrics)
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Optimizing {section_name} section (iteration {iteration})...{Style.RESET_ALL}")
        
        # Create task for the section optimization
        task_id = f"optimize_{section_name.lower().replace(' ', '_')}_{iteration}"
        task = Task(
            content=f"Optimize the {section_name} section based on job analysis",
            id=task_id,
        )
        task.section_name = section_name
        task.section_content = section_content
        task.analysis_results = analysis_results
        
        # Process the task using the workforce
        optimize_result = self.workforce.process_task(task)
        
        # Extract the optimized content
        if hasattr(optimize_result, 'result') and isinstance(optimize_result.result, dict) and 'optimized_content' in optimize_result.result:
            optimized_content = optimize_result.result['optimized_content']
        else:
            # If optimization failed, use original content
            logger.warning(f"Failed to optimize {section_name} section. Using original content.")
            optimized_content = section_content
        
        # Log the optimization result
        self.latex_handler.log_optimization_result(
            section_name=section_name,
            original=section_content,
            optimized=optimized_content,
            analysis_results=analysis_results
        )
        
        # Evaluate the optimization if it's not the last iteration
        if iteration < self.optimization_iterations:
            evaluation_metrics = self._evaluate_optimization(
                section_name=section_name,
                original_content=section_content,
                optimized_content=optimized_content,
                analysis_results=analysis_results
            )
            
            # If the evaluation suggests further improvements, perform refinement
            if evaluation_metrics.get('overall_score', 10) < 8:
                feedback = evaluation_metrics.get('full_evaluation', '')
                optimized_content = self._refine_with_feedback(
                    section_name=section_name,
                    initial_optimization=optimized_content,
                    feedback=feedback,
                    analysis_results=analysis_results
                )
                
                # Update evaluation metrics after refinement
                evaluation_metrics = self._evaluate_optimization(
                    section_name=section_name,
                    original_content=section_content,
                    optimized_content=optimized_content,
                    analysis_results=analysis_results
                )
        else:
            # For the last iteration, we don't need to evaluate
            evaluation_metrics = {}
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ {section_name} section optimization complete{Style.RESET_ALL}")
        
        return optimized_content, evaluation_metrics
    
    def _evaluate_optimization(self, section_name: str, original_content: str, 
                            optimized_content: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the optimization of a section.
        
        Args:
            section_name: Name of the section
            original_content: Original section content
            optimized_content: Optimized section content
            analysis_results: Job description analysis results
            
        Returns:
            Dictionary with evaluation metrics
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Evaluating {section_name} optimization...{Style.RESET_ALL}")
        
        # Create task for the evaluation
        task_id = f"evaluate_{section_name.lower().replace(' ', '_')}"
        task = Task(
            content=f"Evaluate the optimized {section_name} section",
            id=task_id,
        )
        task.section_name = section_name
        task.section_content = original_content
        task.optimized_content = optimized_content
        task.analysis_results = analysis_results
        
        # Process the task using the workforce
        evaluate_result = self.workforce.process_task(task)
        
        # Extract the evaluation metrics
        if hasattr(evaluate_result, 'result') and isinstance(evaluate_result.result, dict):
            evaluation = evaluate_result.result.get('evaluation', '')
            metrics = evaluate_result.result.get('metrics', {})
            metrics['full_evaluation'] = evaluation
        else:
            # If evaluation failed, use empty metrics
            metrics = {'full_evaluation': '', 'overall_score': 5}
        
        if self.verbose:
            overall_score = metrics.get('overall_score', 'N/A')
            print(f"{Fore.GREEN}✅ {section_name} evaluation complete (Score: {overall_score}/10){Style.RESET_ALL}")
        
        return metrics
    
    def _refine_with_feedback(self, section_name: str, initial_optimization: str, 
                          feedback: str, analysis_results: Dict[str, Any]) -> str:
        """Refine an optimization based on feedback.
        
        Args:
            section_name: Name of the section
            initial_optimization: Initial optimized content
            feedback: Evaluation feedback
            analysis_results: Job description analysis results
            
        Returns:
            Refined optimized content
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Refining {section_name} based on feedback...{Style.RESET_ALL}")
        
        # Determine which agent to use based on section name
        if "SKILLS" in section_name.upper():
            refiner = SkillOptimizerAgent(model=self.model, verbose=self.verbose)
            refined_content = refiner.refine_with_feedback(
                initial_optimization=initial_optimization,
                feedback=feedback,
                jd_analysis=analysis_results
            )
        elif "EXPERIENCE" in section_name.upper():
            refiner = ExperienceOptimizerAgent(model=self.model, verbose=self.verbose)
            refined_content = refiner.refine_with_feedback(
                initial_optimization=initial_optimization,
                feedback=feedback,
                jd_analysis=analysis_results
            )
        else:
            # For other sections, create a generic refinement task
            task_id = f"refine_{section_name.lower().replace(' ', '_')}"
            task = Task(
                content=f"Refine the {section_name} section based on feedback",
                id=task_id,
            )
            task.section_name = section_name
            task.initial_optimization = initial_optimization
            task.feedback = feedback
            task.analysis_results = analysis_results
            
            # Process the task using the workforce
            refine_result = self.workforce.process_task(task)
            
            # Extract the refined content
            if hasattr(refine_result, 'result') and isinstance(refine_result.result, dict) and 'refined_content' in refine_result.result:
                refined_content = refine_result.result['refined_content']
            else:
                # If refinement failed, use initial optimization
                refined_content = initial_optimization
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ {section_name} refinement complete{Style.RESET_ALL}")
        
        return refined_content
    
    def _check_ats_compatibility(self, resume_content: str) -> Tuple[int, str, Dict[str, Any]]:
        """Check ATS compatibility of a resume.
        
        Args:
            resume_content: Resume content to check
            
        Returns:
            Tuple of (score, feedback, detailed metrics)
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Checking ATS compatibility...{Style.RESET_ALL}")
        
        # Create ATS compatibility checker
        ats_checker = ATSCompatibilityAgent(model=self.model, verbose=self.verbose)
        
        # Check compatibility
        score, feedback, detailed_metrics = ats_checker.check_compatibility(
            resume_content=resume_content,
            job_description=self.job_description
        )
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ ATS compatibility check complete (Score: {score}/100){Style.RESET_ALL}")
        
        return score, feedback, detailed_metrics
    
    def _assemble_resume(self, original_content: str, optimized_sections: Dict[str, str]) -> str:
        """Assemble the optimized resume.
        
        Args:
            original_content: Original resume content
            optimized_sections: Dictionary mapping section names to optimized content
            
        Returns:
            Assembled resume content
        """
        if self.verbose:
            print(f"{Fore.YELLOW}Assembling optimized resume...{Style.RESET_ALL}")
        
        # Start with the original content
        updated_content = original_content
        
        # Replace each section with its optimized version
        for section_name, section_content in optimized_sections.items():
            updated_content = self.latex_handler.update_section(
                resume_content=updated_content,
                section_name=section_name,
                new_content=section_content
            )
        
        if self.verbose:
            print(f"{Fore.GREEN}✅ Resume assembly complete{Style.RESET_ALL}")
        
        return updated_content
    
    def run(self) -> Dict[str, Any]:
        """Run the resume optimization process using the workforce.
        
        Returns:
            Dictionary with optimization results
        """
        try:
            print(f"{Fore.YELLOW}🚀 Starting Resume Optimization with CAMEL Workforce...{Style.RESET_ALL}")
            
            # Start timing
            start_time = time.time()
            
            # Read the original resume
            original_resume = self.latex_handler.read_resume(self.resume_path)
            
            # Check initial ATS compatibility
            initial_ats_score, initial_feedback, initial_metrics = self._check_ats_compatibility(original_resume)
            self.metrics["ats_scores"]["initial"] = initial_ats_score
            
            # Analyze the job description
            analysis_results = self._analyze_job_description()
            
            # Extract resume sections
            sections = self._extract_resume_sections()
            
            # Optimize each section
            optimized_sections = {}
            
            for section_name in self.sections_to_optimize:
                if section_name in sections:
                    # Get the original section content
                    section_content = sections[section_name]
                    
                    # Optimize the section
                    for iteration in range(1, self.optimization_iterations + 1):
                        # For the first iteration, use the original content
                        # For subsequent iterations, use the previously optimized content
                        current_content = optimized_sections.get(section_name, section_content)
                        
                        # Optimize the section
                        optimized_content, metrics = self._optimize_section(
                            section_name=section_name,
                            section_content=current_content,
                            analysis_results=analysis_results,
                            iteration=iteration
                        )
                        
                        # Store the optimized content and metrics
                        optimized_sections[section_name] = optimized_content
                        
                        # Store metrics for this iteration
                        if section_name not in self.metrics["optimization_metrics"]:
                            self.metrics["optimization_metrics"][section_name] = []
                        
                        self.metrics["optimization_metrics"][section_name].append(metrics)
                    
                    self.metrics["sections_optimized"] += 1
                else:
                    if self.verbose:
                        print(f"{Fore.YELLOW}⚠️ Section '{section_name}' not found in resume{Style.RESET_ALL}")
            
            # Assemble the optimized resume
            optimized_resume = self._assemble_resume(
                original_content=original_resume,
                optimized_sections=optimized_sections
            )
            
            # Save the optimized resume
            self.latex_handler.save_resume(optimized_resume, self.output_path)
            
            # Check final ATS compatibility
            final_ats_score, final_feedback, final_metrics = self._check_ats_compatibility(optimized_resume)
            self.metrics["ats_scores"]["final"] = final_ats_score
            
            # Compare the original and optimized resumes
            comparison_results = self.latex_handler.compare_resumes(
                original_path=self.resume_path,
                optimized_path=self.output_path
            )
            
            # Calculate elapsed time
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.metrics["elapsed_time"] = elapsed_time
            
            # Prepare results
            results = {
                "ats_score": final_ats_score,
                "ats_feedback": final_feedback,
                "initial_ats_score": initial_ats_score,
                "improvement": final_ats_score - initial_ats_score,
                "optimized_sections": list(optimized_sections.keys()),
                "elapsed_time": elapsed_time,
                "comparison": comparison_results,
                "metrics": self.metrics
            }
            
            print(f"{Fore.GREEN}✅ Resume optimization complete! ATS Score: {final_ats_score}/100 (Improved by {final_ats_score - initial_ats_score} points){Style.RESET_ALL}")
            print(f"{Fore.CYAN}📄 Optimized resume saved to {self.output_path}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}⏱️ Optimization completed in {elapsed_time:.2f} seconds{Style.RESET_ALL}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during optimization: {str(e)}", exc_info=True)
            print(f"{Fore.RED}Error during optimization: {str(e)}{Style.RESET_ALL}")
            
            # Try to save partial results
            try:
                if 'optimized_sections' in locals() and isinstance(optimized_sections, dict) and len(optimized_sections) > 0:
                    partial_resume = self._assemble_resume(
                        original_content=self.latex_handler.read_resume(self.resume_path),
                        optimized_sections=optimized_sections
                    )
                    partial_path = f"partial_{self.output_path}"
                    self.latex_handler.save_resume(partial_resume, partial_path)
                    print(f"{Fore.YELLOW}⚠️ Partial results saved to {partial_path}{Style.RESET_ALL}")
            except Exception as save_error:
                logger.error(f"Error saving partial results: {str(save_error)}", exc_info=True)
            
            raise