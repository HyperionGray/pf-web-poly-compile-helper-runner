# Enhanced Workflows

This directory contains the enhanced workflow implementation for the pf task runner.

## Overview

Enhanced workflows provide intelligent, context-aware automation that combines multiple security tools to accomplish complex tasks with minimal user input.

## Core Components

- `workflow_orchestrator.py` - Main orchestration engine
- `target_detector.py` - Intelligent target detection and classification
- `enhanced_fuzzer_selector.py` - Smart fuzzing tool selection
- `enhanced_scanner.py` - Intelligent scanning workflows
- `enhanced_rop.py` - ROP chain generation and exploitation
- `unified_checksec.py` - Unified binary security analysis
- `result_merger.py` - Result aggregation and reporting

## Usage

Enhanced workflows are designed to be used through the pf task runner:

```bash
# Ultimate enhanced workflow - detects and exploits any target
pf hack target=<anything>

# Enhanced binary exploitation
pf pwn target=<binary>

# Enhanced security scanning
pf scan target=<target>

# Enhanced fuzzing
pf fuzz target=<target>
```

## Philosophy

Enhanced workflows follow the "just works" philosophy:
- Minimal configuration required
- Intelligent tool selection
- Context-aware execution
- Comprehensive reporting
- Error recovery and fallbacks