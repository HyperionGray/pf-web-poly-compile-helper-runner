#!/usr/bin/env python3
"""
Setup script for pf-runner
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure we're in the right directory
if not os.path.exists('pf_main.py'):
    print("Error: setup.py must be run from the pf-runner directory")
    sys.exit(1)

# Read version from main module
version = "1.0.0"

# Read long description from README
long_description = ""
readme_path = "README.md"
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="pf-runner",
    version=version,
    description="Polyglot task runner with symbol-free DSL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PF Runner Team",
    author_email="maintainer@example.com",
    url="https://github.com/example/pf-runner",
    license="MIT",
    
    # Package discovery
    packages=find_packages(where="."),
    py_modules=[
        "pf_main",
        "pf_parser", 
        "pf_shell",
        "pf_args",
        "pf_grammar",
        "pf_lark_parser",
        "pf_exceptions",
        "pf_api",
        "pf_tui",
        "pf_containerize",
        "pf_prune"
    ],
    
    # Include non-Python files
    package_data={
        "": [
            "*.pf",
            "*.lark", 
            "*.service",
            "completions/*",
            "assets/**/*",
            "examples/**/*",
            "scripts/*"
        ]
    },
    include_package_data=True,
    
    # Dependencies
    install_requires=[
        "lark>=1.1.0",
        # fabric is bundled, so we don't list it as a dependency
    ],
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Entry points
    entry_points={
        "console_scripts": [
            "pf=pf_main:main",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    
    # Keywords
    keywords="task-runner build-tool polyglot development automation",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/example/pf-runner/issues",
        "Source": "https://github.com/example/pf-runner",
        "Documentation": "https://github.com/example/pf-runner/blob/main/README.md",
    },
)