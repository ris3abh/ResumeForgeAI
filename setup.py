"""Setup script for the resume-optimizer package."""

from setuptools import setup, find_packages

setup(
    name="resume-optimizer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "camel-ai==0.2.44",
        "colorama",
    ],
    entry_points={
        'console_scripts': [
            'resume-optimizer=resume_optimizer.cli:main',
        ],
    },
    author="Resume Optimizer WorkForce",
    author_email="rishabh.sharma1103@gmail.com",
    description="AI-powered resume optimizer that tailors resumes to specific job descriptions",
    keywords="resume, job, AI, optimization, ATS",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Job Seekers",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12.10",
    ],
)