#!/usr/bin/env python3
"""
Setup script for Arisbe: Existential Graphs Implementation
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="arisbe",
    version="1.0.0",
    author="Arisbe Development Team",
    description="Existential Graphs: A Dau-Compliant Implementation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/mijahauan/Arisbe.git",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "hypothesis>=6.88.1",
            "mypy>=1.7.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "pre-commit>=3.5.0",
        ],
        "test": [
            "pytest>=7.4.3",
            "hypothesis>=6.88.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "arisbe-validate=arisbe.tools.validate_corpus:main",
        ],
    },
    include_package_data=True,
    package_data={
        "arisbe": [
            "corpus/**/*",
            "examples/**/*",
            "docs/**/*",
        ],
    },
    zip_safe=False,
)

