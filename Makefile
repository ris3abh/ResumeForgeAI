.PHONY: test clean compile

test:
	python tests/test_resume_customizer.py

clean:
	rm -rf tests/data/output/*

compile:
	cd tests/data/output && pdflatex optimized_resume.tex

all: clean test compile