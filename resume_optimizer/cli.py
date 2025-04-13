#!/usr/bin/env python3
"""ResumeForgeAI: CAMEL-powered resume optimization CLI."""

import os
import sys
import argparse
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

from resume_optimizer.core.workforce_optimizer import WorkforceResumeOptimizer
from resume_optimizer.utils.resume_evaluator import ResumeEvaluator
from resume_optimizer.utils.model_factory import get_model_by_name
from resume_optimizer.core.latex_handler import LatexHandler


def main():
    """Main function to run the resume optimizer with CAMEL Workforce."""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="ResumeForgeAI: CAMEL-powered resume optimizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--resume", required=True, help="Path to the LaTeX resume file")
    parser.add_argument("--job-description", required=True, help="Path to the job description file")
    parser.add_argument("--output", default="optimized_resume.tex", 
                     help="Output path for the optimized resume")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation step")
    parser.add_argument("--model", default=None, 
                     help="Model to use (e.g., gpt-4o-mini, gpt-4o, gpt-3.5-turbo)")
    parser.add_argument("--sections", default=None, 
                     help="Comma-separated list of sections to optimize")
    parser.add_argument("--iterations", type=int, default=2, 
                     help="Number of optimization iterations to perform")
    parser.add_argument("--quiet", action="store_true", 
                     help="Reduce verbosity of output")
    parser.add_argument("--report", action="store_true", 
                     help="Generate a detailed optimization report")
    
    args = parser.parse_args()
    
    # Print welcome message
    print("\n" + "="*80)
    print(f"{Fore.CYAN}ResumeForgeAI - CAMEL-powered Resume Optimizer{Style.RESET_ALL}")
    print("="*80 + "\n")
    
    # Check if files exist
    resume_path = Path(args.resume)
    job_desc_path = Path(args.job_description)
    
    if not resume_path.exists():
        print(f"{Fore.RED}ERROR: Resume file not found: {args.resume}{Style.RESET_ALL}")
        return 1
    
    if not job_desc_path.exists():
        print(f"{Fore.RED}ERROR: Job description file not found: {args.job_description}{Style.RESET_ALL}")
        return 1
    
    # Read job description from file
    try:
        with open(job_desc_path, 'r') as f:
            job_description = f.read()
    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to read job description: {str(e)}{Style.RESET_ALL}")
        return 1
    
    # Create output directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = f"debug_output_{timestamp}"
    os.makedirs(debug_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Process sections list if provided
    sections_to_optimize = None
    if args.sections:
        sections_to_optimize = [s.strip() for s in args.sections.split(",")]
        print(f"{Fore.YELLOW}Will optimize these sections: {', '.join(sections_to_optimize)}{Style.RESET_ALL}")
    
    # Initialize model
    model = None
    if args.model:
        try:
            model = get_model_by_name(args.model)
            print(f"{Fore.GREEN}Using model: {args.model}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Failed to initialize model {args.model}, using default model instead.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Error: {str(e)}{Style.RESET_ALL}")
    
    # Log start time
    start_time = time.time()
    print(f"{Fore.YELLOW}Starting resume optimization at {datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}")
    
    try:
        # Create and run the optimizer
        optimizer = WorkforceResumeOptimizer(
            resume_path=str(resume_path),
            job_description=job_description,
            output_path=args.output,
            model=model,
            debug_mode=args.debug,
            verbose=not args.quiet,
            sections_to_optimize=sections_to_optimize,
            optimization_iterations=args.iterations
        )
        
        # Run optimization
        results = optimizer.run()
        
        # Log completion time
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"{Fore.GREEN}Resume optimization completed in {elapsed:.2f} seconds{Style.RESET_ALL}")
        
        # Display ATS score improvement
        initial_score = results.get('initial_ats_score', 0)
        final_score = results.get('ats_score', 0)
        improvement = final_score - initial_score
        
        print(f"\n{Fore.CYAN}▓▓▓▓▓ ATS Compatibility Results ▓▓▓▓▓{Style.RESET_ALL}")
        print(f"Initial ATS Score: {initial_score}/100")
        print(f"Final ATS Score: {final_score}/100")
        print(f"Improvement: {improvement:+d} points")
        
        # Save results to file
        if args.report:
            report_path = f"optimization_report_{timestamp}.json"
            with open(report_path, 'w') as f:
                # Convert any non-serializable values to strings
                json_compatible_results = json.dumps(results, default=str)
                f.write(json_compatible_results)
            
            print(f"\n{Fore.GREEN}Detailed optimization report saved to {report_path}{Style.RESET_ALL}")
        
        # Run evaluation if not skipped
        if not args.skip_eval:
            print(f"\n{Fore.YELLOW}Starting evaluation...{Style.RESET_ALL}")
            evaluator = ResumeEvaluator(
                original_resume_path=str(resume_path),
                optimized_resume_path=args.output,
                job_description_path=str(job_desc_path)
            )
            
            evaluation_results = evaluator.run_evaluation()
            
            eval_end_time = time.time()
            eval_elapsed = eval_end_time - end_time
            print(f"{Fore.GREEN}Evaluation completed in {eval_elapsed:.2f} seconds{Style.RESET_ALL}")
            
            # Save evaluation results to file
            eval_report_path = f"evaluation_report_{timestamp}.json"
            with open(eval_report_path, 'w') as f:
                # Convert any non-serializable values to strings
                json_compatible_eval = json.dumps(evaluation_results, default=str)
                f.write(json_compatible_eval)
            
            print(f"{Fore.GREEN}Evaluation report saved to {eval_report_path}{Style.RESET_ALL}")
        
        # Generate summary table
        print("\n" + "="*80)
        print(f"{Fore.CYAN}▓▓▓▓▓ OPTIMIZATION SUMMARY ▓▓▓▓▓{Style.RESET_ALL}")
        print(f"Resume: {resume_path}")
        print(f"Optimized Resume: {args.output}")
        print(f"ATS Score Improvement: {initial_score} → {final_score} ({improvement:+d})")
        print(f"Optimized Sections: {', '.join(results.get('optimized_sections', []))}")
        print(f"Total Time: {elapsed:.2f} seconds")
        print("="*80 + "\n")
        
        # Print optimization tips based on ATS feedback
        if 'ats_feedback' in results and results['ats_feedback']:
            print(f"\n{Fore.YELLOW}▓▓▓▓▓ OPTIMIZATION TIPS ▓▓▓▓▓{Style.RESET_ALL}")
            feedback = results['ats_feedback']
            # Break feedback into lines and limit to first 5 tips
            feedback_lines = [line.strip() for line in feedback.split('\n') if line.strip()]
            for i, line in enumerate(feedback_lines[:5]):
                if len(line) > 100:
                    line = line[:97] + "..."
                print(f"{i+1}. {line}")
            if len(feedback_lines) > 5:
                print(f"... plus {len(feedback_lines)-5} more tips (see full report)")
            print()
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Optimization process interrupted by user.{Style.RESET_ALL}")
        return 130
        
    except Exception as e:
        print(f"\n{Fore.RED}ERROR: {str(e)}{Style.RESET_ALL}")
        if args.debug:
            traceback.print_exc()
        
        # Save error to log file
        error_log_path = f"logs/error_{timestamp}.log" 
        with open(error_log_path, 'w') as f:
            f.write(f"Error: {str(e)}\n\n")
            f.write(traceback.format_exc())
        
        print(f"{Fore.RED}Error details saved to {error_log_path}{Style.RESET_ALL}")
        return 1


def print_section_header(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
    print("="*80)


if __name__ == "__main__":
    sys.exit(main())