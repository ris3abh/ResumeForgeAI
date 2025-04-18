#!/usr/bin/env python3
"""
Test Script for Resume Customizer

This script tests the resume customization system on a sample resume and job description.
"""

import os
import sys
import time
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.job_analyzer import analyze_job_description
from agents.resume_parser import parse_resume
from agents.optimizer import optimize_resume


def setup_test_environment():
    """Set up the test environment."""
    # Create output directory if it doesn't exist
    output_dir = Path("tests/data/output")
    output_dir.mkdir(exist_ok=True, parents=True)
    return output_dir


def load_test_data():
    """Load the test resume and job description."""
    # Load resume from tests directory
    resume_path = Path("tests/data/test_resumes/resume.tex")
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")
    
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_content = f.read()
    
    # Load job description from tests directory
    job_desc_path = Path("tests/data/test_job_descriptions/job_description.txt")
    if not job_desc_path.exists():
        raise FileNotFoundError(f"Job description file not found: {job_desc_path}")
    
    with open(job_desc_path, 'r', encoding='utf-8') as f:
        job_description = f.read()
    
    return resume_content, job_description


def test_job_analyzer(job_description, output_dir):
    """Test the job analyzer module."""
    print("\n=== Testing Job Analyzer ===")
    start_time = time.time()
    
    job_requirements = analyze_job_description(job_description)
    
    # Save the results
    requirements_path = output_dir / "job_requirements.txt"
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write(job_requirements)
    
    print(f"Job analysis completed in {time.time() - start_time:.2f} seconds")
    print(f"Results saved to: {requirements_path}")
    
    return job_requirements


def test_resume_parser(resume_content, output_dir):
    """Test the resume parser module."""
    print("\n=== Testing Resume Parser ===")
    start_time = time.time()
    
    resume_structure = parse_resume(resume_content)
    
    # Save the results
    structure_path = output_dir / "resume_structure.txt"
    with open(structure_path, 'w', encoding='utf-8') as f:
        f.write(str(resume_structure))
    
    print(f"Resume parsing completed in {time.time() - start_time:.2f} seconds")
    print(f"Results saved to: {structure_path}")
    
    # Also save the extracted sections
    if resume_structure["experience_section"]:
        with open(output_dir / "experience_section.tex", 'w', encoding='utf-8') as f:
            f.write(resume_structure["experience_section"]["content"])
    
    if resume_structure["skills_section"]:
        with open(output_dir / "skills_section.tex", 'w', encoding='utf-8') as f:
            f.write(resume_structure["skills_section"]["content"])
    
    return resume_structure


def test_optimizer(resume_content, resume_structure, job_requirements, output_dir):
    """Test the resume optimizer module."""
    print("\n=== Testing Resume Optimizer ===")
    start_time = time.time()
    
    # Import validation function
    from utils.latex_utils import compare_latex_structure
    
    # Optimize the resume
    optimized_resume = optimize_resume(resume_content, resume_structure, job_requirements)
    
    # Validate the LaTeX syntax
    is_valid, issues = compare_latex_structure(resume_content, optimized_resume)
    
    if not is_valid:
        print("⚠️ Warning: LaTeX validation issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        
        # Try to fix the issues (simplified approach)
        from utils.latex_utils import fix_latex_issues
        optimized_resume = fix_latex_issues(optimized_resume, resume_content)
        
        # Check again after fixes
        is_valid, issues = compare_latex_structure(resume_content, optimized_resume)
        if is_valid:
            print("✅ Issues fixed successfully!")
        else:
            print("⚠️ Some issues could not be fixed automatically.")
    else:
        print("✅ LaTeX structure validation passed!")
    
    # Save the optimized resume
    optimized_path = output_dir / "optimized_resume.tex"
    with open(optimized_path, 'w', encoding='utf-8') as f:
        f.write(optimized_resume)
    
    # Also save a diff for easy review
    diff_path = output_dir / "resume_diff.txt"
    import difflib
    diff = difflib.unified_diff(
        resume_content.splitlines(),
        optimized_resume.splitlines(),
        lineterm='',
        fromfile='original',
        tofile='optimized'
    )
    with open(diff_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(diff))
    
    print(f"Resume optimization completed in {time.time() - start_time:.2f} seconds")
    print(f"Optimized resume saved to: {optimized_path}")
    print(f"Diff saved to: {diff_path}")
    
    return optimized_resume


def run_tests():
    """Run all tests."""
    print("Starting Resume Customizer tests...")
    
    # Setup
    output_dir = setup_test_environment()
    resume_content, job_description = load_test_data()
    
    # Run tests
    job_requirements = test_job_analyzer(job_description, output_dir)
    resume_structure = test_resume_parser(resume_content, output_dir)
    optimized_resume = test_optimizer(resume_content, resume_structure, job_requirements, output_dir)
    
    print("\n=== Testing Complete ===")
    print(f"All output files can be found in: {output_dir}")
    
    return {
        "job_requirements": job_requirements,
        "resume_structure": resume_structure,
        "optimized_resume": optimized_resume
    }


if __name__ == "__main__":
    run_tests()