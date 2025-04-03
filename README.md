## Resume Optimizer

An AI-powered resume optimizer that tailors your resume to specific job descriptions, improving your chances of getting past ATS (Applicant Tracking Systems) and catching the attention of recruiters.

#### Features

- ✅ Job Description Analysis: Extracts key skills, requirements, and keywords from job descriptions
- ✅ Resume Customization: Optimizes your technical skills and work experience sections
- ✅ Iterative Improvement: Uses feedback to refine resume sections
- ✅ ATS Compatibility Check: Evaluates how well your resume will perform with ATS systems

#### Installation

From PyPI (Coming Soon)

```bash
pip install resume-optimizer
```

From Source

```bash
git clone https://github.com/ris3abh/ResumeForgeAI.git
cd ResumeForgeAI
pip install -e .
```

Usage

- Command Line
```bash
resume-optimizer --resume path/to/your/resume.tex --job-description path/to/job_description.txt --output optimized_resume.tex
```

- As a Python Package
```bash
pythonCopyfrom resume_optimizer.core.optimizer import ResumeOptimizer
```

# Initialize the optimizer

```bash
optimizer = ResumeOptimizer(
    resume_path="path/to/your/resume.tex",
    job_description="Job description text...",
    output_path="optimized_resume.tex"
)
```

# Run the optimization
```bash
optimizer.run()
Requirements
```

Python 3.9+

LaTeX resume template in a compatible format
CAMEL AI package (automatically installed)

How It Works

Job Description Analysis: The system analyzes the job description to extract key skills, requirements, and keywords.
Initial Optimization: Technical skills and work experience sections are optimized based on the job analysis.
Evaluation: The optimized sections are evaluated against the job requirements.
Refinement: Based on evaluation feedback, sections are further refined.
ATS Check: The final resume is checked for ATS compatibility.
