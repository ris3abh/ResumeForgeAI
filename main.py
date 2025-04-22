#!/usr/bin/env python3
"""
ResumeForgeAI - An agent-based resume customization system
"""

import argparse
import sys
import logging
from pathlib import Path

from camel.models import ModelFactory
from camel.types import ModelPlatformType
from camel.types import ModelType

from agents.job_analyzer import analyze_job_description, create_job_analyzer_agent
from agents.resume_parser import parse_resume, create_resume_parser_agent
from agents.deductive_reasoner import deduce_optimization_strategy, create_deductive_reasoner_agent
from agents.coordinator import coordinate_optimization, create_coordinator_agent
from agents.optimizer import optimize_resume, create_optimizer_agent
from agents.critic import critique_resume, create_critic_agent, extract_rating
from agents.agent_communication import ResumeForgeWorkforce
from utils.latex_utils import fix_latex_issues, compare_latex_structure, enhance_resume_bullet_points

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ResumeForgeAI - Agent-based Resume Customization System')
    parser.add_argument('--resume', type=str, required=True, 
                        help='Path to LaTeX resume file')
    parser.add_argument('--job', type=str, required=True, 
                        help='Path to job description file')
    parser.add_argument('--output', type=str, default='optimized_resume.tex',
                        help='Output file path for optimized resume')
    parser.add_argument('--iterations', type=int, default=2,
                        help='Number of optimization iterations')
    parser.add_argument('--model', type=str, default='gpt-4o-mini',
                        help='Model to use for agents')
    parser.add_argument('--use-workforce', action='store_true',
                        help='Use the Workforce framework for agent collaboration')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate input files
    resume_path = Path(args.resume)
    job_path = Path(args.job)
    
    if not resume_path.exists():
        logger.error(f"Resume file not found: {resume_path}")
        sys.exit(1)
        
    if not job_path.exists():
        logger.error(f"Job description file not found: {job_path}")
        sys.exit(1)
    
    # Read input files
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_content = f.read()
    
    with open(job_path, 'r', encoding='utf-8') as f:
        job_description = f.read()
    
    # Initialize the model
    logger.info(f"Initializing model: {args.model}")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,  # Specify the platform
        model_type=args.model,
)
    
    if args.use_workforce:
        # Use the Workforce framework for agent collaboration
        logger.info("Using Workforce framework for agent collaboration")
        optimize_with_workforce(resume_content, job_description, args.output, 
                               args.iterations, model)
    else:
        # Use direct agent communication
        logger.info("Using direct agent communication")
        optimize_with_direct_communication(resume_content, job_description, 
                                          args.output, args.iterations, model)

def optimize_with_direct_communication(resume_content, job_description, output_path, 
                                      iterations, model):
    """
    Optimize a resume using direct agent communication.
    
    Args:
        resume_content (str): The LaTeX resume content
        job_description (str): The job description
        output_path (str): Path to save the optimized resume
        iterations (int): Number of optimization iterations
        model: Model to use for agents
    """
    logger.info("Starting resume optimization with direct agent communication")
    
    # Step 1: Analyze job description
    logger.info("Step 1: Analyzing job description...")
    job_analyzer = create_job_analyzer_agent(model)
    job_requirements = analyze_job_description(job_description, job_analyzer)
    logger.info("Job requirements analysis complete")
    
    # Step 2: Parse resume
    logger.info("Step 2: Parsing resume structure...")
    resume_parser = create_resume_parser_agent(model)
    resume_structure = parse_resume(resume_content, resume_parser)
    logger.info("Resume parsing complete")
    
    # Step 3: Get deductive insights
    logger.info("Step 3: Deducing optimization strategy...")
    deductive_agent = create_deductive_reasoner_agent(model)
    optimization_strategy = deduce_optimization_strategy(
        job_requirements, resume_structure, deductive_agent
    )
    logger.info("Deductive reasoning complete")
    
    # Step 4: Get coordination plan
    logger.info("Step 4: Coordinating optimization strategy...")
    coordinator_agent = create_coordinator_agent(model)
    coordination_plan = coordinate_optimization(
        resume_structure, job_requirements, coordinator_agent
    )
    logger.info("Coordination planning complete")
    
    # Step 5: Optimize resume
    logger.info("Step 5: Starting optimization iterations...")
    optimizer_agent = create_optimizer_agent(model)
    critic_agent = create_critic_agent(model)
    
    # Initial optimization
    optimized_resume = optimize_resume(
        resume_content, 
        resume_structure, 
        job_requirements,
        str(optimization_strategy),
        coordination_plan.get("priorities", {}).keys(),
        optimizer_agent
    )
    
    # Iterative optimization based on feedback
    for iteration in range(iterations - 1):
        logger.info(f"Iteration {iteration + 1} of {iterations - 1}")
        
        # Get critique
        feedback = critique_resume(
            resume_content, optimized_resume, job_requirements, critic_agent
        )
        logger.info(f"Critique received with rating: {extract_rating(feedback)}")
        
        # Apply feedback to improve specific sections
        updated_resume = optimize_resume(
            optimized_resume, 
            resume_structure, 
            job_requirements,
            str(optimization_strategy) + "\n\nCritic Feedback:\n" + feedback,
            coordination_plan.get("priorities", {}).keys(),
            optimizer_agent
        )
        
        # Validate LaTeX structure
        is_valid, issues = compare_latex_structure(resume_content, updated_resume)
        if not is_valid:
            logger.warning("LaTeX validation issues detected, fixing...")
            for issue in issues:
                logger.warning(f"Issue: {issue}")
            updated_resume = fix_latex_issues(updated_resume, resume_content)
        
        optimized_resume = updated_resume
    
    # Apply final enhancements
    optimized_resume = enhance_resume_bullet_points(optimized_resume)
    
    # Write the optimized resume
    logger.info(f"Writing optimized resume to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(optimized_resume)
    
    logger.info("Resume optimization complete")

def optimize_with_workforce(resume_content, job_description, output_path, 
                           iterations, model):
    """
    Optimize a resume using the Workforce framework.
    
    Args:
        resume_content (str): The LaTeX resume content
        job_description (str): The job description
        output_path (str): Path to save the optimized resume
        iterations (int): Number of optimization iterations
        model: Model to use for agents
    """
    logger.info("Starting resume optimization with Workforce framework")
    
    # Create a workforce
    workforce = ResumeForgeWorkforce("Resume Customization System")
    
    # Add worker agents to the workforce
    workforce.add_worker(
        "Analyzes job descriptions to extract key requirements and keywords",
        worker=create_job_analyzer_agent(model)
    ).add_worker(
        "Parses LaTeX resumes to identify sections and structure",
        worker=create_resume_parser_agent(model)
    ).add_worker(
        "Makes logical connections between job requirements and resume content",
        worker=create_deductive_reasoner_agent(model)
    ).add_worker(
        "Coordinates the resume customization process",
        worker=create_coordinator_agent(model)
    ).add_worker(
        "Optimizes resume content to match job requirements",
        worker=create_optimizer_agent(model)
    ).add_worker(
        "Critiques optimized resumes and provides feedback",
        worker=create_critic_agent(model)
    )
    
    # Create sequential tasks
    tasks = []
    
    # Task 1: Analyze job description
    job_analysis_task = workforce.create_task(
        f"Analyze this job description: {job_description[:1000]}...",
        "job_analysis"
    )
    tasks.append(job_analysis_task)
    
    # Task 2: Parse resume
    resume_parsing_task = workforce.create_task(
        f"Parse this LaTeX resume: {resume_content[:1000]}...",
        "resume_parsing"
    )
    tasks.append(resume_parsing_task)
    
    # Process initial tasks to get job requirements and resume structure
    initial_results = workforce.process_sequential_tasks(tasks[:2])
    job_requirements = initial_results[job_analysis_task.id]
    resume_structure = initial_results[resume_parsing_task.id]
    
    # Task 3: Deduce optimization strategy
    deduction_task = workforce.create_task(
        f"Deduce optimization strategy:\nJob Requirements: {job_requirements}\nResume Structure: {resume_structure}",
        "deduction"
    )
    tasks.append(deduction_task)
    
    # Task 4: Coordinate optimization
    coordination_task = workforce.create_task(
        f"Coordinate optimization:\nJob Requirements: {job_requirements}\nResume Structure: {resume_structure}",
        "coordination"
    )
    tasks.append(coordination_task)
    
    # Process strategy tasks
    strategy_results = workforce.process_sequential_tasks(tasks[2:4])
    optimization_strategy = strategy_results[deduction_task.id]
    coordination_plan = strategy_results[coordination_task.id]
    
    # Task 5: Initial optimization
    optimization_task = workforce.create_task(
        f"Optimize resume:\nResume: {resume_content[:1000]}...\nJob Requirements: {job_requirements}\nStrategy: {optimization_strategy}\nPlan: {coordination_plan}",
        "optimization"
    )
    tasks.append(optimization_task)
    
    # Process optimization task
    optimized_resume = workforce.process_task(optimization_task)
    
    # Iterative optimization based on feedback
    for iteration in range(iterations - 1):
        logger.info(f"Iteration {iteration + 1} of {iterations - 1}")
        
        # Task: Critique the resume
        critique_task = workforce.create_task(
            f"Critique resume:\nOriginal: {resume_content[:500]}...\nOptimized: {optimized_resume[:500]}...\nJob Requirements: {job_requirements}",
            f"critique_{iteration}"
        )
        
        # Process critique task
        feedback = workforce.process_task(critique_task)
        
        # Task: Apply feedback
        refinement_task = workforce.create_task(
            f"Refine resume based on feedback:\nResume: {optimized_resume[:1000]}...\nFeedback: {feedback}\nJob Requirements: {job_requirements}",
            f"refinement_{iteration}"
        )
        
        # Process refinement task
        updated_resume = workforce.process_task(refinement_task)
        
        # Validate LaTeX structure
        is_valid, issues = compare_latex_structure(resume_content, updated_resume)
        if not is_valid:
            logger.warning("LaTeX validation issues detected, fixing...")
            for issue in issues:
                logger.warning(f"Issue: {issue}")
            updated_resume = fix_latex_issues(updated_resume, resume_content)
        
        optimized_resume = updated_resume
    
    # Apply final enhancements
    optimized_resume = enhance_resume_bullet_points(optimized_resume)
    
    # Write the optimized resume
    logger.info(f"Writing optimized resume to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(optimized_resume)
    
    logger.info("Resume optimization complete")

if __name__ == "__main__":
    main()