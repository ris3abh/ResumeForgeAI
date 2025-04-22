.PHONY: install test clean optimize format

# Variables
PYTHON = python
PYTEST = pytest
RESUME_PATH = test_data/resume.tex
JOB_DESC_PATH = test_data/job_description.txt
OUTPUT_PATH = test_data/optimized_resume.tex
MODEL = gpt-4o-mini
ITERATIONS = 2

# Installation
install:
	pip install -r requirements.txt

# Testing
test:
	$(PYTHON) -m tests.test_resumeforge
	$(PYTHON) -m tests.test_resume_customizer

# Resume optimization
optimize:
	$(PYTHON) main.py --resume $(RESUME_PATH) --job $(JOB_DESC_PATH) --output $(OUTPUT_PATH) --model $(MODEL) --iterations $(ITERATIONS)

# Resume optimization with Workforce
optimize-workforce:
	$(PYTHON) main.py --resume $(RESUME_PATH) --job $(JOB_DESC_PATH) --output $(OUTPUT_PATH) --model $(MODEL) --iterations $(ITERATIONS) --use-workforce

# Clean output files
clean:
	rm -f $(OUTPUT_PATH)
	rm -rf tests/data/output/*

# Compile LaTeX resume to PDF
compile:
	cd $(dir $(OUTPUT_PATH)) && pdflatex $(notdir $(OUTPUT_PATH))

# Run full workflow
full-workflow: clean optimize compile

# Format code
format:
	black .