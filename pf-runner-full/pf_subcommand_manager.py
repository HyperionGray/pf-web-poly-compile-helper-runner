#!/usr/bin/env python3
"""
pf_subcommand_manager.py - Subcommand discovery and management for pf

This module provides:
- Subcommand discovery from included files
- Include file parsing and loading
- Subcommand registration with argument parser

Extracted from pf_main.py to follow Single Responsibility Principle.
"""

import os
import sys
from typing import List, Dict, Optional

# Import existing pf functionality
from pf_parser import (
    _load_pfy_source_with_includes, parse_pfyfile_text
)


class SubcommandManager:
    """Manages subcommand discovery and registration."""
    
    def __init__(self):
        pass
        
    def discover_subcommands(self, pfyfile: Optional[str] = None) -> Dict[str, List[str]]:
        """Discover subcommands from included files.

        Uses the task->source-file map produced during include expansion, which
        is more reliable than re-parsing include directives after expansion.
        """
        subcommands: Dict[str, List[str]] = {}
        
        try:
            _dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfyfile)

            # Group task names by the file they came from.
            for task_name, source_file in task_sources.items():
                subcommands.setdefault(source_file, []).append(task_name)

            for source_file in subcommands:
                subcommands[source_file].sort()
                    
        except FileNotFoundError:
            # If the main Pfyfile is not found, that's expected in some cases
            # (e.g., using always-available tasks only), so don't warn
            pass
        except Exception as e:
            # Only warn for unexpected errors during discovery
            # This shouldn't prevent the tool from working
            print(f"Warning: Could not discover subcommands: {e}", file=sys.stderr)
            
        return subcommands
    
    def register_subcommands_with_parser(self, arg_parser, pfyfile: Optional[str] = None):
        """Register discovered subcommands with the argument parser."""
        subcommands = self.discover_subcommands(pfyfile)
        
        for include_file, task_names in subcommands.items():
            try:
                arg_parser.add_subcommand_from_file(include_file, task_names)
            except Exception as e:
                print(f"Warning: Could not register subcommands from {include_file}: {e}", file=sys.stderr)
    
    def _extract_include_files(self, dsl_src: str) -> List[str]:
        """Extract include file paths from DSL source."""
        include_files = []
        
        for line in dsl_src.split('\n'):
            line = line.strip()
            if line.startswith('include '):
                # Extract the include path
                include_path = line[8:].strip()
                # Remove quotes if present
                if include_path.startswith('"') and include_path.endswith('"'):
                    include_path = include_path[1:-1]
                elif include_path.startswith("'") and include_path.endswith("'"):
                    include_path = include_path[1:-1]
                include_files.append(include_path)
                
        return include_files
    
    def _load_include_file(self, include_path: str, pfyfile: Optional[str] = None) -> str:
        """Load content from an include file."""
        # Handle relative paths
        if not os.path.isabs(include_path):
            # Make relative to the main Pfyfile or current directory
            if pfyfile:
                pfy_resolved = os.path.abspath(pfyfile)
                base_dir = os.path.dirname(pfy_resolved)
            else:
                base_dir = os.getcwd()
                
            full_path = os.path.join(base_dir, include_path)
        else:
            full_path = include_path
            
        # Handle special case where pfyfile is resolved but include_path is relative to it
        if not os.path.exists(full_path) and pfyfile:
            pfy_resolved = os.path.abspath(pfyfile)
            if os.path.exists(pfy_resolved):
                base_dir = os.path.dirname(os.path.abspath(pfy_resolved))
            full_path = os.path.join(base_dir, include_path)
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
