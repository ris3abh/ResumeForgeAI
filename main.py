#!/usr/bin/env python3
"""
Resume Customizer - First Iteration
A system to optimize a LaTeX resume for a specific job description.
"""

import argparse
import sys
from pathlib import Path

from agents.job_analyzer import analyze_job_description
from agents.resume_parser import parse_resume
from agents.optimizer import optimize_resume


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Resume Customization System')
    parser.add_argument('--resume', type=str, required=True, 
                        help='Path to LaTeX resume file')
    parser.add_argument('--job', type=str, required=True, 
                        help='Path to job description file')
    parser.add_argument('--output', type=str, default='optimized_resume.tex',
                        help='Output file path for optimized resume')
    args = parser.parse_args()
    
    # Validate input files
    resume_path = Path(args.resume)
    job_path = Path(args.job)
    
    if not resume_path.exists():
        print(f"Error: Resume file not found: {resume_path}")
        sys.exit(1)
        
    if not job_path.exists():
        print(f"Error: Job description file not found: {job_path}")
        sys.exit(1)
    
    # Read input files
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_content = f.read()
    
    with open(job_path, 'r', encoding='utf-8') as f:
        job_description = f.read()
    
    print("Step 1: Analyzing job description...")
    job_requirements = analyze_job_description(job_description)
    
    print("Step 2: Parsing resume...")
    resume_structure = parse_resume(resume_content)
    
    print("Step 3: Optimizing resume...")
    optimized_resume = optimize_resume(resume_content, resume_structure, job_requirements)
    
    print("Step 4: Writing optimized resume...")
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(optimized_resume)
    
    print(f"Successfully created optimized resume: {args.output}")


if __name__ == "__main__":
    main()