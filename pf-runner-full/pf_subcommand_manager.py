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
    _find_pfyfile, _load_pfy_source_with_includes, parse_pfyfile_text
)


class SubcommandManager:
    """Manages subcommand discovery and registration."""

    _ROOT_FLAT_MODULES = frozenset({"always-available", "module-compat"})
    
    def __init__(self):
        pass

    def _module_name_from_source_file(self, source_file: Optional[str]) -> Optional[str]:
        """Convert a `Pfyfile.<name>.pf` path into a normalized module name."""
        if not source_file:
            return None

        basename = os.path.basename(source_file)
        if not (basename.startswith("Pfyfile.") and basename.endswith(".pf")):
            return None

        module_name = basename[len("Pfyfile.") : -len(".pf")].replace("_", "-").lower()
        if module_name in ("", "pf"):
            return None
        return module_name

    def _pick_module_source(
        self,
        current_source: Optional[str],
        candidate_source: Optional[str],
    ) -> Optional[str]:
        """Prefer a stable, shallow source path when a module spans multiple files."""
        if not candidate_source:
            return current_source
        if not current_source:
            return candidate_source
        return min(
            (current_source, candidate_source),
            key=lambda path: (len(path.split(os.sep)), path),
        )
        
    def discover_subcommands(self, pfyfile: Optional[str] = None) -> Dict[str, List[str]]:
        """Discover subcommands from included files.

        Uses the task->source-file map produced during include expansion, which
        is more reliable than re-parsing include directives after expansion.
        """
        subcommands: Dict[str, List[str]] = {}
        
        try:
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfyfile)
            dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)

            resolved_pfyfile = _find_pfyfile(file_arg=pfyfile)
            main_pfyfile = (
                os.path.abspath(resolved_pfyfile)
                if resolved_pfyfile and os.path.exists(resolved_pfyfile)
                else None
            )
            main_module_name = (
                self._module_name_from_source_file(main_pfyfile) if main_pfyfile else None
            )
            is_root = main_module_name is None
            module_entries: Dict[str, Dict[str, object]] = {}

            for task_name, task in sorted(dsl_tasks.items()):
                source_file = os.path.abspath(task.source_file) if task.source_file else None
                if main_pfyfile and source_file == main_pfyfile:
                    continue

                module_name = self._module_name_from_source_file(source_file)
                if not module_name:
                    continue
                if main_module_name and module_name == main_module_name:
                    continue
                if is_root and module_name in self._ROOT_FLAT_MODULES:
                    continue

                entry = module_entries.setdefault(
                    module_name,
                    {"tasks": [], "source_file": None},
                )
                entry["tasks"].append(task_name)
                entry["source_file"] = self._pick_module_source(
                    entry["source_file"], source_file
                )

            for entry in module_entries.values():
                source_file = entry["source_file"]
                if not source_file:
                    continue
                subcommands[source_file] = sorted(entry["tasks"])
                    
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
