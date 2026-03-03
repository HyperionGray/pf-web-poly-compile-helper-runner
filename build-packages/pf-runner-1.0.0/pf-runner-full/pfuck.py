#!/usr/bin/env python3
"""
pfuck.py - Autocorrect functionality for pf tasks

This module provides intelligent suggestions for failed pf commands,
similar to "thefuck" but specific to pf tasks and workflows.
"""

import os
import sys
import re
import difflib
import subprocess
from typing import List, Dict, Optional, Tuple, Set
import shlex


class PfAutocorrect:
    """Autocorrect engine for pf commands."""
    
    def __init__(self, pfyfile: Optional[str] = None):
        self.pfyfile = pfyfile
        self._task_cache = None
        self._subcommand_cache = None
        
    def get_available_tasks(self) -> Dict[str, List[str]]:
        """Get all available tasks organized by source."""
        if self._task_cache is not None:
            return self._task_cache
            
        tasks = {
            'main': [],
            'subcommands': {}
        }
        
        try:
            # Get task list from pf
            cmd = ['python3', 'pf_parser.py', 'list']
            if self.pfyfile:
                cmd.extend(['--file', self.pfyfile])
                
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                # Parse the output to extract task names
                current_section = 'main'
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    # Look for task names (usually indented or have specific format)
                    if line.startswith('  ') or line.startswith('- '):
                        task_name = line.strip('- ').split()[0]
                        if task_name and not task_name.startswith('['):
                            tasks[current_section].append(task_name)
                    elif ':' in line and not line.startswith(' '):
                        # Might be a section header
                        section_name = line.split(':')[0].lower()
                        if section_name not in tasks['subcommands']:
                            tasks['subcommands'][section_name] = []
                        current_section = section_name
                        
        except Exception as e:
            print(f"Warning: Could not load tasks: {e}", file=sys.stderr)
            
        self._task_cache = tasks
        return tasks
    
    def get_all_task_names(self) -> List[str]:
        """Get flat list of all available task names."""
        tasks = self.get_available_tasks()
        all_tasks = []
        
        all_tasks.extend(tasks['main'])
        for subcommand_tasks in tasks['subcommands'].values():
            all_tasks.extend(subcommand_tasks)
            
        return list(set(all_tasks))  # Remove duplicates
    
    def get_subcommands(self) -> List[str]:
        """Get list of available subcommands."""
        if self._subcommand_cache is not None:
            return self._subcommand_cache
            
        subcommands = ['list', 'help', 'run']  # Built-in commands
        
        try:
            # Try to detect subcommands from included files
            tasks = self.get_available_tasks()
            subcommands.extend(tasks['subcommands'].keys())
            
        except Exception:
            pass
            
        self._subcommand_cache = list(set(subcommands))
        return self._subcommand_cache
    
    def suggest_task_correction(self, failed_task: str, context: Optional[str] = None) -> List[str]:
        """Suggest corrections for a failed task name."""
        all_tasks = self.get_all_task_names()
        
        # Use difflib for fuzzy matching
        suggestions = difflib.get_close_matches(
            failed_task, all_tasks, n=5, cutoff=0.4
        )
        
        # Add some custom logic for common mistakes
        custom_suggestions = self._get_custom_suggestions(failed_task, all_tasks)
        
        # Combine and deduplicate
        all_suggestions = suggestions + custom_suggestions
        seen = set()
        final_suggestions = []
        for suggestion in all_suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                final_suggestions.append(suggestion)
                
        return final_suggestions[:5]  # Limit to top 5
    
    def _get_custom_suggestions(self, failed_task: str, all_tasks: List[str]) -> List[str]:
        """Get custom suggestions based on common patterns."""
        suggestions = []
        
        # Common typos and patterns
        patterns = [
            # Hyphen/underscore confusion
            (lambda x: x.replace('-', '_'), "hyphen to underscore"),
            (lambda x: x.replace('_', '-'), "underscore to hyphen"),
            
            # Case variations
            (lambda x: x.lower(), "lowercase"),
            (lambda x: x.upper(), "uppercase"),
            (lambda x: x.title(), "title case"),
            
            # Common abbreviations
            (lambda x: x.replace('dev', 'development'), "dev expansion"),
            (lambda x: x.replace('development', 'dev'), "dev abbreviation"),
            (lambda x: x.replace('prod', 'production'), "prod expansion"),
            (lambda x: x.replace('production', 'prod'), "prod abbreviation"),
            (lambda x: x.replace('test', 'testing'), "test expansion"),
            (lambda x: x.replace('testing', 'test'), "test abbreviation"),
            
            # Build/compile variations
            (lambda x: x.replace('build', 'compile'), "build to compile"),
            (lambda x: x.replace('compile', 'build'), "compile to build"),
            (lambda x: x.replace('make', 'build'), "make to build"),
            (lambda x: x.replace('build', 'make'), "build to make"),
        ]
        
        for transform, description in patterns:
            try:
                transformed = transform(failed_task)
                if transformed != failed_task and transformed in all_tasks:
                    suggestions.append(transformed)
            except Exception:
                continue
                
        return suggestions
    
    def suggest_command_correction(self, failed_command: str) -> List[str]:
        """Suggest corrections for a complete failed command."""
        suggestions = []
        
        # Parse the command
        try:
            parts = shlex.split(failed_command)
        except ValueError:
            parts = failed_command.split()
            
        if not parts:
            return ["pf list  # Show available tasks"]
            
        # Remove 'pf' if it's the first part
        if parts[0] == 'pf':
            parts = parts[1:]
            
        if not parts:
            return ["pf list  # Show available tasks"]
            
        # Check if first part is a subcommand
        subcommands = self.get_subcommands()
        first_part = parts[0]
        
        if first_part in subcommands:
            # It's a valid subcommand, check the task name
            if len(parts) > 1:
                task_suggestions = self.suggest_task_correction(parts[1])
                for suggestion in task_suggestions:
                    suggestions.append(f"pf {first_part} {suggestion}")
            else:
                suggestions.append(f"pf {first_part} --help  # Show {first_part} tasks")
        else:
            # Check if it's a misspelled subcommand
            subcommand_suggestions = difflib.get_close_matches(
                first_part, subcommands, n=3, cutoff=0.5
            )
            
            for sub_suggestion in subcommand_suggestions:
                if len(parts) > 1:
                    suggestions.append(f"pf {sub_suggestion} {' '.join(parts[1:])}")
                else:
                    suggestions.append(f"pf {sub_suggestion}")
            
            # Check if it's a task name (assume 'run' subcommand)
            task_suggestions = self.suggest_task_correction(first_part)
            for task_suggestion in task_suggestions:
                if len(parts) > 1:
                    suggestions.append(f"pf run {task_suggestion} {' '.join(parts[1:])}")
                else:
                    suggestions.append(f"pf run {task_suggestion}")
        
        # Add some general helpful suggestions
        if not suggestions:
            suggestions.extend([
                "pf list  # Show all available tasks",
                "pf help  # Show general help",
                f"pf help {first_part}  # Show help for '{first_part}' if it exists"
            ])
            
        return suggestions[:5]
    
    def analyze_error_context(self, error_output: str) -> Dict[str, str]:
        """Analyze error output to provide context-aware suggestions."""
        context = {}
        
        # Common error patterns
        if "no such task" in error_output.lower():
            context['error_type'] = 'unknown_task'
        elif "command not found" in error_output.lower():
            context['error_type'] = 'command_not_found'
        elif "permission denied" in error_output.lower():
            context['error_type'] = 'permission_denied'
            context['suggestion'] = 'Try adding --sudo flag'
        elif "connection" in error_output.lower() and "refused" in error_output.lower():
            context['error_type'] = 'connection_refused'
            context['suggestion'] = 'Check host connectivity and SSH configuration'
        elif "file not found" in error_output.lower():
            context['error_type'] = 'file_not_found'
            
        return context
    
    def get_last_failed_command(self) -> Optional[str]:
        """Try to get the last failed command from shell history."""
        try:
            # Try to read from bash history
            history_file = os.path.expanduser("~/.bash_history")
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    lines = f.readlines()
                    
                # Look for recent pf commands
                for line in reversed(lines[-100:]):  # Check last 100 commands
                    line = line.strip()
                    if line.startswith('pf '):
                        return line
                        
        except Exception:
            pass
            
        return None


def main():
    """Main entry point for pfuck command."""
    from pf_args import create_pfuck_parser
    
    parser = create_pfuck_parser()
    args = parser.parse_args()
    
    autocorrect = PfAutocorrect(args.file)
    
    if args.list:
        print("Available tasks:")
        tasks = autocorrect.get_available_tasks()
        
        if tasks['main']:
            print("\nMain tasks:")
            for task in sorted(tasks['main']):
                print(f"  {task}")
                
        for subcommand, sub_tasks in tasks['subcommands'].items():
            if sub_tasks:
                print(f"\n{subcommand} tasks:")
                for task in sorted(sub_tasks):
                    print(f"  {task}")
        return 0
    
    # Get the command to correct
    if args.command:
        failed_command = args.command
    else:
        failed_command = autocorrect.get_last_failed_command()
        if not failed_command:
            print("No failed command found. Specify a command to correct or use --list to see available tasks.")
            return 1
            
    print(f"Analyzing failed command: {failed_command}")
    
    # Get suggestions
    suggestions = autocorrect.suggest_command_correction(failed_command)
    
    if not suggestions:
        print("No suggestions found. Use 'pf list' to see available tasks.")
        return 1
        
    print("\nSuggested corrections:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")
        
    # Interactive selection
    if args.execute:
        if len(suggestions) == 1:
            selected = suggestions[0]
        else:
            try:
                choice = input(f"\nSelect correction (1-{len(suggestions)}, or Enter to cancel): ").strip()
                if not choice:
                    return 0
                    
                choice_num = int(choice)
                if 1 <= choice_num <= len(suggestions):
                    selected = suggestions[choice_num - 1]
                else:
                    print("Invalid selection.")
                    return 1
            except (ValueError, KeyboardInterrupt):
                return 0
                
        print(f"\nExecuting: {selected}")
        return os.system(selected)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())