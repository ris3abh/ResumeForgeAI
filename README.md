# Enhanced ResumeForgeAI System

This is an enhanced version of the ResumeForgeAI system with multi-agent collaborative resume customization.

## New Features

The enhanced system adds the following capabilities:

1. **Orchestrator Agent**: Coordinates the entire customization process
2. **Work Experience Customization Agent**: Tailors work experience bullet points
3. **Skills Customization Agent**: Optimizes the skills section for the job
4. **LaTeX Validation Agent**: Ensures proper LaTeX formatting
5. **Compliance Verification Agent**: Checks if all job requirements are met
6. **Agent Communication**: Agents can collaborate and provide feedback to each other
7. **Parallel Processing**: Multiple agents can work simultaneously
8. **Feedback Loops**: Validation and refinement loops for quality control

## Architecture

The system uses a multi-agent architecture with inter-agent communication:

```
                                      ┌────────────────────┐
                                      │                    │
                                   ┌──┤ Resume Analyzer    │
                                   │  │                    │
                                   │  └────────────────────┘
                                   │
                                   ▼
┌────────────────────┐            ┌────────────────────┐
│                    │            │                    │
│ Job Description    │────────────┤ Orchestrator       ├────┐
│ Analyzer           │            │ Agent              │    │
│                    │            │                    │    │
└────────────────────┘            └────────────────────┘    │
                                   │                        │
                                   │                        │
               ┌───────────────────┬──────────────────┐     │
               │                   │                  │     │
               ▼                   ▼                  ▼     │
  ┌────────────────────┐  ┌────────────────────┐  ┌─────────┴──────────┐
  │                    │  │                    │  │                    │
  │ Work Experience    │  │ Skills             │  │ Compliance         │
  │ Customization      │  │ Customization      │  │ Verification       │
  │                    │  │                    │  │                    │
  └────────────────────┘  └────────────────────┘  └────────────────────┘
             │                     │                      │
             │                     │                      │
             ▼                     ▼                      │
  ┌────────────────────┐  ┌────────────────────┐          │
  │                    │  │                    │          │
  │ LaTeX Validation   │◄─┤ LaTeX Validation   │          │
  │ (Work Experience)  │  │ (Skills)           │          │
  │                    │  │                    │          │
  └────────────────────┘  └────────────────────┘          │
             │                     │                      │
             │                     │                      │
             └─────────┬───────────┘                      │
                       │                                  │
                       ▼                                  │
             ┌────────────────────┐                       │
             │                    │                       │
             │ Resume Generation  │◄──────────────────────┘
             │                    │
             └────────────────────┘
```

## Setup

1. Make sure you have installed all dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key in a `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Enhanced System

Run the system using the same command as before:

```bash
python resumeforegerai/main.py --resume data/sample_resume.tex --job data/sample_job_description.txt --verbose
```

## Output

The system will generate:

1. `output/resume_analysis.json`: Analysis of the original resume
2. `output/job_analysis.json`: Analysis of the job description
3. `output/task_plan.json`: Orchestration plan for customization
4. `output/compliance_verification.json`: Compliance verification results
5. `output/tailored_resume.tex`: The final tailored resume

## Agent Communication

The enhanced system features collaborative communication between agents. Each agent:

1. Documents its reasoning and decisions
2. Provides feedback on other agents' outputs
3. Refines its work based on feedback
4. Contributes to the overall goal of tailoring the resume

## Configuration

You can customize agent behaviors by modifying the JSON files in `config/agents/`.

## Adding New Agents

To add a new agent:

1. Create a new agent implementation in the `agents/` directory
2. Add configuration in `config/agents/`
3. Update `config/phases.json` to include the new agent in the workflow
4. Update `workflow/graph.py` to handle the new phase
5. Update `workflow/state.py` to store the new agent's output