# resume_optimizer/cli.py
#!/usr/bin/env python3
"""Script to run the resume optimizer with debugging output and evaluation."""

import os
import argparse
import time
import traceback
from colorama import Fore, Style, init

# Initialize colorama
init()

from resume_optimizer.core.workforce_optimizer import WorkforceResumeOptimizer
from resume_optimizer.utils.resume_evaluator import ResumeEvaluator


def main():
    """Main function to run the resume optimizer with debugging."""
    parser = argparse.ArgumentParser(description="Run resume optimizer with CAMEL Workforce")
    parser.add_argument("--resume", required=True, help="Path to the LaTeX resume file")
    parser.add_argument("--job-description", required=True, help="Path to the job description file")
    parser.add_argument("--output", default="optimized_resume.tex", 
                       help="Output path for the optimized resume")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation step")
    parser.add_argument("--model", default=None, help="Model to use (default: GPT-4O-mini)")
    
    args = parser.parse_args()
    
    # Read job description from file
    with open(args.job_description, 'r') as f:
        job_description = f.read()
    
    # Create output directories
    os.makedirs("debug_output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Log start time
    start_time = time.time()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    print(f"{Fore.YELLOW}[{timestamp}] Starting resume optimization with CAMEL Workforce{Style.RESET_ALL}")
    
    try:
        # Create and run the optimizer
        optimizer = WorkforceResumeOptimizer(
            resume_path=args.resume,
            job_description=job_description,
            output_path=args.output,
            debug_mode=args.debug
        )
        
        # Run optimization
        results = optimizer.run()
        
        # Log completion time
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"{Fore.GREEN}[{timestamp}] Resume optimization completed in {elapsed:.2f} seconds{Style.RESET_ALL}")
        
        # Display ATS score
        ats_score = results.get('ats_score', 'N/A')
        print(f"{Fore.CYAN}ATS Compatibility Score: {ats_score}/100{Style.RESET_ALL}")
        
        # Run evaluation if not skipped
        if not args.skip_eval:
            print(f"{Fore.YELLOW}[{timestamp}] Starting evaluation{Style.RESET_ALL}")
            evaluator = ResumeEvaluator(
                original_resume_path=args.resume,
                optimized_resume_path=args.output,
                job_description_path=args.job_description
            )
            evaluator.run_evaluation()
            
            eval_end_time = time.time()
            eval_elapsed = eval_end_time - end_time
            print(f"{Fore.GREEN}[{timestamp}] Evaluation completed in {eval_elapsed:.2f} seconds{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}{Style.RESET_ALL}")
        traceback.print_exc()
        
        # Save error to log file
        error_log_path = f"logs/error_{timestamp}.log"
        with open(error_log_path, 'w') as f:
            f.write(f"Error: {str(e)}\n\n")
            f.write(traceback.format_exc())
        
        print(f"{Fore.RED}Error details saved to {error_log_path}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()