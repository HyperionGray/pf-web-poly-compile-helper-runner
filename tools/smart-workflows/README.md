# Smart Workflows - Intelligent Tool Integration

This directory contains the smart workflow system that intelligently combines multiple security, debugging, and exploitation tools into cohesive, adaptive workflows.

## Overview

The smart workflow system addresses the key issues in the original tool collection:

1. **Tool Redundancy** - Eliminates duplicate functionality by creating unified tools
2. **Fragmented Workflows** - Chains tools together intelligently based on target analysis
3. **Complex Task Proliferation** - Replaces 178+ individual tasks with smart adaptive workflows
4. **Missing Integration** - Enables automatic escalation from reconnaissance to exploitation

## Core Components

### 1. Target Detection (`target_detector.py`)
- Automatically detects target types (binary, web app, kernel module, etc.)
- Analyzes target characteristics and properties
- Recommends appropriate workflows and tools

### 2. Unified Binary Analysis (`unified_checksec.py`)
- Consolidates all checksec implementations into a single authoritative tool
- Enhanced security feature detection (RELRO, canary, NX, PIE, FORTIFY, etc.)
- Vulnerability pattern detection and risk scoring

### 3. Smart ROP Analysis (`smart_rop.py`)
- Intelligently selects between ROPgadget and ropper based on binary characteristics
- Analyzes ROP potential and gadget quality
- Generates exploitation recommendations based on findings

## Smart Workflows Available

### Master Workflows (Auto-detect and execute)
- `pf hack target=<target>` - Ultimate smart workflow for any target
- `pf pwn target=<binary>` - Smart binary exploitation
- `pf scan target=<target>` - Smart security scanning
- `pf fuzz target=<target>` - Smart fuzzing

### Specialized Workflows
- `pf smart-analyze target=<target>` - Comprehensive analysis
- `pf smart-binary-analysis binary=<file>` - Binary security analysis
- `pf smart-web-security url=<url>` - Web security pipeline
- `pf smart-exploit target=<binary>` - Exploit development

### Utilities
- `pf smart-detect target=<target>` - Target type detection
- `pf smart-help` - Show smart workflow help

## Examples

### Binary Exploitation Workflow
```bash
# Detect and analyze binary
pf smart-detect target=./vulnerable_binary
pf smart-binary-analysis binary=./vulnerable_binary

# Generate exploit
pf smart-exploit target=./vulnerable_binary
```

### Web Application Security
```bash
# Comprehensive web security testing
pf smart-web-security url=https://example.com
```

The smart workflow system transforms the complex collection of individual security tools into an intelligent, integrated platform that automatically selects, chains, and correlates tools to provide comprehensive security analysis with minimal user effort.