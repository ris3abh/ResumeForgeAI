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
import logging
import hashlib
import concurrent.futures
from typing import Dict, Any
from dotenv import load_dotenv

# Disable __pycache__ directories
sys.dont_write_bytecode = True

from workflow.graph import ResumeAutomationWorkflow
from utils.file_utils import read_text_file, write_text_file, read_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('output/workflow.log', mode='w')
    ]
)
logger = logging.getLogger("ResumeForgeAI")

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
    
    parser.add_argument(
        "--compliance-threshold", 
        type=int,
        default=90,
        help="Compliance score threshold to exit with success (0-100)"
    )
    
    parser.add_argument(
        "--disable-cache", 
        action="store_true",
        help="Disable caching of resume analysis"
    )
    
    parser.add_argument(
        "--disable-parallel", 
        action="store_true",
        help="Disable parallel processing"
    )
    
    return parser.parse_args()


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        "data",
        "output",
        "config/agents",
        "cache"
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
        logger.error("The following required files are missing:")
        for file in missing_files:
            logger.error(f"  - {file}")
        logger.error("Please create these files before running the application.")
        sys.exit(1)


def get_resume_hash(resume_file: str) -> str:
    """Generate a hash of the resume file for caching."""
    with open(resume_file, 'rb') as file:
        file_content = file.read()
        return hashlib.md5(file_content).hexdigest()


def load_cached_resume_analysis(resume_hash: str) -> Dict[str, Any]:
    """Load cached resume analysis if available."""
    cache_file = f"cache/resume_{resume_hash}.json"
    if os.path.exists(cache_file):
        logger.info(f"Loading cached resume analysis")
        with open(cache_file, 'r') as file:
            return json.load(file)
    return None


def save_resume_analysis_cache(resume_hash: str, analysis: Dict[str, Any]):
    """Save resume analysis to cache."""
    cache_file = f"cache/resume_{resume_hash}.json"
    with open(cache_file, 'w') as file:
        json.dump(analysis, file)
    logger.info(f"Saved resume analysis to cache: {cache_file}")


def print_agent_message(agent_name: str, message: str, is_response: bool = False):
    """Print a formatted agent message."""
    if is_response:
        print(f"\n\033[1;36m[{agent_name} RESPONSE]\033[0m")
    else:
        print(f"\n\033[1;34m[{agent_name} REQUEST]\033[0m")
    
    print(f"{message}")
    print("\033[1;30m" + "-" * 80 + "\033[0m")


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
    
    # Print compliance information
    if result.get("compliance_verification"):
        compliance = result["compliance_verification"]
        print(f"\n✅ Compliance Verification:")
        print(f"   - Overall compliance score: {compliance.get('compliance_score', 0)}/100")
        print(f"   - Requirement compliance: {compliance.get('requirement_compliance_percentage', 0):.1f}%")
        print(f"   - Keyword compliance: {compliance.get('keyword_compliance_percentage', 0):.1f}%")
        
        if verbose:
            missing_reqs = compliance.get("missing_requirements", [])
            if missing_reqs:
                print("\n   Missing Requirements:")
                for req in missing_reqs[:3]:
                    print(f"     - {req}")
                if len(missing_reqs) > 3:
                    print(f"     ... and {len(missing_reqs) - 3} more")
    
    # Print output file locations
    print("\n📂 Output Files:")
    output_files = [
        ("Resume Analysis", "output/resume_analysis.json"),
        ("Job Analysis", "output/job_analysis.json"),
        ("Workflow Log", "output/workflow.log")
    ]
    
    if result.get("tailored_resume"):
        output_files.append(("Tailored Resume", "output/tailored_resume.tex"))
    
    for desc, path in output_files:
        if os.path.exists(path):
            print(f"   - {desc}: {path}")


def main():
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv(override=True)
    
    # Parse arguments
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Ensure directories exist
    ensure_directories()
    
    # Check required files
    check_required_files(args.resume, args.job)
    
    # Check for OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        logger.error("Please set your OpenAI API key in the .env file.")
        sys.exit(1)
    
    # Validate API key format
    if not openai_api_key.startswith(("sk-", "sk-org-")):
        logger.warning("Your OpenAI API key doesn't appear to be in the expected format.")
        logger.warning("Expected format: sk-... or sk-org-...")
        logger.warning(f"Current key (first 5 chars): {openai_api_key[:5]}...")
        logger.warning("Continuing anyway, but this might cause authentication issues.")
    
    print("\n" + "="*80)
    print("Resume Automation System")
    print("="*80)
    print(f"\nBase Resume: {args.resume}")
    print(f"Job Description: {args.job}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Model: GPT-4o (OpenAI)")
    print(f"Compliance Threshold: {args.compliance_threshold}/100")
    print(f"Parallel Processing: {'Disabled' if args.disable_parallel else 'Enabled'}")
    print(f"Caching: {'Disabled' if args.disable_cache else 'Enabled'}")
    
    # Initialize and run the workflow
    print("\nInitializing workflow...")
    try:
        # Test OpenAI connection before proceeding
        from utils.openai_client import test_openai_connection
        test_openai_connection()
        
        # Create the workflow
        workflow = ResumeAutomationWorkflow(
            show_agent_messages=True,
            early_exit_compliance_score=args.compliance_threshold,
            enable_parallel=not args.disable_parallel,
            verbose=args.verbose
        )
        
        # Check if we have a cached resume analysis
        resume_analysis = None
        if not args.disable_cache:
            resume_hash = get_resume_hash(args.resume)
            resume_analysis = load_cached_resume_analysis(resume_hash)
        
        print("Running workflow...")
        result = workflow.run(args.resume, args.job, cached_resume_analysis=resume_analysis)
        
        # Cache the resume analysis if not already cached
        if not args.disable_cache and resume_analysis is None and result.get("resume_analysis"):
            resume_hash = get_resume_hash(args.resume)
            save_resume_analysis_cache(resume_hash, result["resume_analysis"])
        
        # Print results
        print_workflow_result(result, args.verbose)
        
    except Exception as e:
        logger.error(f"Error initializing workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\nWorkflow complete!")


if __name__ == "__main__":
    main()