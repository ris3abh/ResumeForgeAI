#!/usr/bin/env python3
"""Test script for ResumeForgeAI optimization."""

import os
import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Add proper error handling for imports
try:
    # Import the main optimizer
    from resume_optimizer import optimize_resume
except ImportError as e:
    print(f"{Fore.RED}Error importing resume_optimizer: {str(e)}{Style.RESET_ALL}")
    print("Make sure you're running this script from the project root and have installed the package (pip install -e .)")
    sys.exit(1)

def main():
    """Run a test optimization."""
    
    # Define paths
    resume_path = "test_data/resume.tex"
    job_description_path = "test_data/jd.txt"
    output_path = "test_optimized_resume.tex"
    
    print(f"{Fore.CYAN}Testing ResumeForgeAI optimization...{Style.RESET_ALL}")
    print(f"Resume: {resume_path}")
    print(f"Job Description: {job_description_path}")
    print(f"Output: {output_path}")
    
    # Check if API key is set
    if "OPENAI_API_KEY" not in os.environ:
        print(f"{Fore.RED}ERROR: OPENAI_API_KEY environment variable not set{Style.RESET_ALL}")
        print(f"Please set your OpenAI API key with: export OPENAI_API_KEY=your_key_here")
        return 1
    
    # Check if files exist
    if not Path(resume_path).exists():
        print(f"{Fore.RED}ERROR: Resume file not found: {resume_path}{Style.RESET_ALL}")
        return 1
    
    if not Path(job_description_path).exists():
        print(f"{Fore.RED}ERROR: Job description file not found: {job_description_path}{Style.RESET_ALL}")
        return 1
    
    # Run the optimization
    try:
        results = optimize_resume(
            resume_path=resume_path,
            job_description_path=job_description_path,
            output_path=output_path,
            verbose=True,
            debug_mode=True,
            sections=["TECHNICAL SKILLS"],  # Just optimize one section for faster testing
            iterations=1  # Use a single iteration for faster testing
        )
        
        # Print results summary
        print(f"\n{Fore.GREEN}Test completed successfully!{Style.RESET_ALL}")
        print(f"ATS Score: {results.get('ats_score', 'N/A')}")
        print(f"Improvement: {results.get('improvement', 'N/A')}")
        print(f"Optimized resume saved to: {output_path}")
        
        return 0
    
    except Exception as e:
        print(f"{Fore.RED}ERROR: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())