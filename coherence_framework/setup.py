#!/usr/bin/env python3
"""
AI Coherence Framework - Standalone Package Setup

A comprehensive framework for maintaining codebase coherence when projects
exceed AI assistant context windows. Prevents reinvention, maintains quality,
and enables graceful recovery from development excursions.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-coherence-framework",
    version="1.0.0",
    author="AI Development Team",
    description="Coherence maintenance framework for large codebases exceeding AI context",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: Documentation",
    ],
    python_requires=">=3.8",
    install_requires=[
        "coverage>=7.0.0",
        "vulture>=2.0.0",
        "mypy>=1.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "isort>=5.0.0",
        "bandit>=1.7.0",
        "radon>=6.0.0",
        "networkx>=3.0.0",
        "pydeps>=3.0.0",
        "pyyaml>=6.0.0",
        "pathlib2>=2.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pre-commit>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "coherence-init=coherence_framework.cli:init_project",
            "coherence-check=coherence_framework.cli:check_coherence",
            "coherence-commit=coherence_framework.cli:smart_commit",
            "coherence-session=coherence_framework.cli:session_manager",
        ],
    },
    include_package_data=True,
    package_data={
        "coherence_framework": [
            "templates/*",
            "hooks/*",
            "configs/*",
        ],
    },
)
