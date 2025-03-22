# Resume Automation System

A multi-agent workflow system for analyzing and tailoring resumes based on job descriptions.

## Overview

This system uses a multi-agent architecture built with LangGraph to automate the process of analyzing resumes and job descriptions, and providing tailored recommendations for resume customization.

### Features

- **LaTeX Resume Analysis**: Automatically analyzes the structure and components of LaTeX resumes
- **Job Description Analysis**: Identifies key requirements and keywords from job descriptions
- **Tailoring Recommendations**: Provides specific recommendations for customizing resumes
- **Modular Architecture**: Easily extensible with additional agents and phases
- **Configuration-driven**: Workflow and agent behaviors are controlled via JSON configuration

## Directory Structure

```
resume_automation/
│
├── config/                        # Configuration files
│   ├── phases.json                # Workflow phase definitions
│   └── agents/                    # Agent-specific configurations
│       ├── resume_analyzer.json   # Resume analyzer agent config
│       ├── job_analyzer.json      # Job description analyzer agent config
│       └── resume_generator.json  # Resume generator agent config
│
├── data/                          # Input data files
│   ├── sample_resume.tex          # Base resume template
│   └── sample_job_description.txt # Sample job description
│
├── agents/                        # Agent implementations
│   ├── resume_analyzer.py         # Resume analysis implementation
│   ├── job_analyzer.py            # Job analysis implementation
│   └── resume_generator.py        # Resume generation implementation
│
├── utils/                         # Utility functions
│   ├── file_utils.py              # File reading/writing utilities
│   └── latex_utils.py             # LaTeX handling utilities
│
├── workflow/                      # Workflow definitions
│   ├── graph.py                   # LangGraph setup and workflow
│   └── state.py                   # State definitions
│
├── output/                        # Output directory for results
│
├── main.py                        # Main entry point
└── requirements.txt               # Dependencies
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/resume-automation.git
   cd resume-automation
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Place your LaTeX resume in the `data` directory or specify its path with `--resume`.
2. Place your job description in the `data` directory or specify its path with `--job`.
3. Run the system:
   ```
   python main.py --resume data/your_resume.tex --job data/your_job_description.txt --verbose
   ```

4. View the results in the `output` directory.

## Configuration

### Adding or Modifying Phases

Edit the `config/phases.json` file to modify the workflow phases.

### Customizing Agent Behavior

Edit the agent configuration files in `config/agents/` to customize:
- Model parameters (temperature, etc.)
- System prompts
- Function definitions

## Future Enhancements

1. Implement the Resume Generator agent to automatically create tailored resumes
2. Add a web interface for easier interaction
3. Support for additional resume formats (Word, Markdown, etc.)
4. Integration with job platforms to automatically fetch job descriptions

## License

MIT