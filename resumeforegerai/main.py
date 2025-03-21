#!/usr/bin/env python3
"""
Resume Automation System
------------------------
Multi-agent workflow for analyzing and tailoring resumes based on job descriptions.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any

from workflow.graph import ResumeAutomationWorkflow
from utils.file_utils import read_text_file, write_text_file, read_json_file


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Resume Automation System - Multi-agent workflow for resume tailoring"
    )
    
    parser.add_argument(
        "--resume", 
        type=str, 
        default="data/sample_resume.tex",
        help="Path to the base LaTeX resume file"
    )
    
    parser.add_argument(
        "--job", 
        type=str, 
        default="data/sample_job_description.txt",
        help="Path to the job description file"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="output",
        help="Directory for output files"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        "data",
        "output",
        "config/agents"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def check_required_files(resume_file: str, job_description_file: str):
    """Check that required files exist."""
    missing_files = []
    
    if not os.path.exists(resume_file):
        missing_files.append(resume_file)
    
    if not os.path.exists(job_description_file):
        missing_files.append(job_description_file)
    
    # Check configuration files
    config_files = [
        "config/phases.json",
        "config/agents/resume_analyzer.json",
        "config/agents/job_analyzer.json"
    ]
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            missing_files.append(config_file)
    
    if missing_files:
        print("Error: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease create these files before running the application.")
        sys.exit(1)


def print_workflow_result(result: Dict[str, Any], verbose: bool = False):
    """Print the workflow result."""
    print("\n" + "="*80)
    print("Resume Automation Workflow Complete")
    print("="*80)
    
    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
        return
    
    print(f"\n✅ Completed phases: {', '.join(result['completed_phases'])}")
    
    # Print resume analysis summary
    if result.get("resume_analysis"):
        sections = result["resume_analysis"].get("sections", [])
        print(f"\n📄 Resume Analysis:")
        print(f"   - Identified {len(sections)} sections")
        if verbose:
            for section in sections:
                print(f"     - {section.get('name', 'Unnamed Section')}")
    
    # Print job analysis summary
    if result.get("job_analysis"):
        structured_recs = result["job_analysis"].get("structured_recommendations", {})
        key_requirements = structured_recs.get("key_requirements", [])
        keywords = structured_recs.get("keywords", [])
        
        print(f"\n🔍 Job Description Analysis:")
        print(f"   - Identified {len(key_requirements)} key requirements")
        print(f"   - Extracted {len(keywords)} important keywords")
        
        if verbose and key_requirements:
            print("\n   Key Requirements:")
            for i, req in enumerate(key_requirements[:5], 1):
                print(f"     {i}. {req}")
            if len(key_requirements) > 5:
                print(f"     ... and {len(key_requirements) - 5} more")
        
        if verbose and keywords:
            print("\n   Important Keywords:")
            print(f"     {', '.join(keywords[:10])}")
            if len(keywords) > 10:
                print(f"     ... and {len(keywords) - 10} more")
    
    # Print output file locations
    print("\n📂 Output Files:")
    output_files = [
        ("Resume Analysis", "output/resume_analysis.json"),
        ("Job Analysis", "output/job_analysis.json")
    ]
    
    if result.get("tailored_resume"):
        output_files.append(("Tailored Resume", "output/tailored_resume.tex"))
    
    for desc, path in output_files:
        if os.path.exists(path):
            print(f"   - {desc}: {path}")


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Ensure directories exist
    ensure_directories()
    
    # Check required files
    check_required_files(args.resume, args.job)
    
    print("\n" + "="*80)
    print("Resume Automation System")
    print("="*80)
    print(f"\nBase Resume: {args.resume}")
    print(f"Job Description: {args.job}")
    print(f"Output Directory: {args.output_dir}")
    
    # Initialize and run the workflow
    print("\nInitializing workflow...")
    workflow = ResumeAutomationWorkflow()
    
    print("Running workflow...")
    result = workflow.run(args.resume, args.job)
    
    # Print results
    print_workflow_result(result, args.verbose)
    
    print("\nWorkflow complete!")


if __name__ == "__main__":
    main()