"""Command-line interface for the resume optimizer."""

import argparse
from resume_optimizer.core.optimizer import ResumeOptimizer


def main():
    """Main function to run the resume optimizer from command line.
    
    This function parses command-line arguments and runs the resume optimization
    process with the provided parameters.
    """
    parser = argparse.ArgumentParser(description="Optimize a resume for a specific job description")
    parser.add_argument("--resume", required=True, help="Path to the LaTeX resume file")
    parser.add_argument("--job-description", required=True, help="Path to the job description file")
    parser.add_argument("--output", default="optimized_resume.tex", 
                       help="Output path for the optimized resume")
    
    args = parser.parse_args()
    
    # Read job description from file
    with open(args.job_description, 'r') as f:
        job_description = f.read()
    
    # Create and run the optimizer
    optimizer = ResumeOptimizer(
        resume_path=args.resume,
        job_description=job_description,
        output_path=args.output
    )
    
    optimizer.run()
    print(f"Resume optimization complete. Optimized resume saved to {args.output}")


if __name__ == "__main__":
    main()