#!/usr/bin/env python3
"""
pf_builtin_commands.py - Built-in command handlers for pf

This module provides:
- Built-in command implementations (list, help, prune, debug-on, debug-off)
- Command-specific logic and formatting
- Integration with pf core functionality

Extracted from pf_main.py to follow Single Responsibility Principle.
"""

import os
import sys
import shlex
from typing import List, Dict, Optional

# Import existing pf functionality
from pf_parser import (
    _find_pfyfile, _load_pfy_source_with_includes, parse_pfyfile_text,
    get_alias_map
)
from pf_prune import prune_containers
from pf_exceptions import format_exception_for_user


class BuiltinCommandHandler:
    """Handles execution of built-in pf commands."""
    
    def __init__(self):
        pass
    
    def handle_prune_command(self, args) -> int:
        """Handle the prune command."""
        try:
            prune_containers()
            return 0
        except Exception as e:
            print(format_exception_for_user(e), file=sys.stderr)
            return 1
    
    def handle_debug_on_command(self, args) -> int:
        """Handle the debug-on command."""
        try:
            debug_file = os.path.expanduser("~/.pf_debug")
            with open(debug_file, 'w') as f:
                f.write("1")
            print("Debug mode enabled. Set PF_DEBUG=1 in your environment or run with --debug.")
            return 0
        except Exception as e:
            print(f"Failed to enable debug mode: {e}", file=sys.stderr)
            return 1
    
    def handle_debug_off_command(self, args) -> int:
        """Handle the debug-off command."""
        try:
            debug_file = os.path.expanduser("~/.pf_debug")
            if os.path.exists(debug_file):
                os.remove(debug_file)
            print("Debug mode disabled.")
            return 0
        except Exception as e:
            print(f"Failed to disable debug mode: {e}", file=sys.stderr)
            return 1
    
    def handle_list_command(self, args) -> int:
        """Handle the list command."""
        try:
            # Find and load the Pfyfile
            pfyfile = _find_pfyfile(args.file)
            if not pfyfile:
                print("No Pfyfile found. Create a Pfyfile.pf to define tasks.", file=sys.stderr)
                return 1
            
            # Load and parse the Pfyfile
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=args.file)
            tasks = parse_pfyfile_text(dsl_src, task_sources)
            
            if not tasks:
                print("No tasks found in Pfyfile.")
                return 0
            
            # Load aliases
            try:
                alias_map = get_alias_map(file_arg=args.file)
            except Exception:
                alias_map = {}
            
            # Create reverse alias map for display
            reverse_aliases = {}
            for alias, task in alias_map.items():
                if task not in reverse_aliases:
                    reverse_aliases[task] = []
                reverse_aliases[task].append(alias)
            
            print("Available tasks:")
            for task_name in sorted(tasks.keys()):
                task = tasks[task_name]
                
                # Get task description
                description = ""
                if hasattr(task, 'description') and task.description:
                    description = task.description
                elif hasattr(task, 'commands') and task.commands:
                    # Use first command as description if no explicit description
                    first_cmd = task.commands[0] if task.commands else ""
                    if len(first_cmd) > 50:
                        description = first_cmd[:47] + "..."
                    else:
                        description = first_cmd
                
                # Format task line
                task_line = f"  {task_name}"
                
                # Add aliases if any
                if task_name in reverse_aliases:
                    aliases_str = ", ".join(reverse_aliases[task_name])
                    task_line += f" (aliases: {aliases_str})"
                
                # Add description
                if description:
                    task_line += f" - {description}"
                
                print(task_line)
            
            return 0
            
        except Exception as e:
            print(format_exception_for_user(e), file=sys.stderr)
            return 1
    
    def handle_help_command(self, args) -> int:
        """Handle the help command."""
        if hasattr(args, 'task') and args.task:
            # Show help for specific task
            return self._show_task_help(args.task, args.file)
        else:
            # Show general help
            return self._show_general_help()
    
    def _show_task_help(self, task_name: str, file_arg: Optional[str]) -> int:
        """Show help for a specific task."""
        try:
            # Find and load the Pfyfile
            pfyfile = _find_pfyfile(file_arg)
            if not pfyfile:
                print("No Pfyfile found.", file=sys.stderr)
                return 1
            
            # Load and parse the Pfyfile
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
            tasks = parse_pfyfile_text(dsl_src, task_sources)
            
            if task_name not in tasks:
                print(f"Task '{task_name}' not found.", file=sys.stderr)
                return 1
            
            task = tasks[task_name]
            
            print(f"Task: {task_name}")
            
            # Show description
            if hasattr(task, 'description') and task.description:
                print(f"Description: {task.description}")
            
            # Show commands
            if hasattr(task, 'commands') and task.commands:
                print("Commands:")
                for i, cmd in enumerate(task.commands, 1):
                    print(f"  {i}. {cmd}")
            
            # Show environment variables
            if hasattr(task, 'env') and task.env:
                print("Environment variables:")
                for key, value in task.env.items():
                    print(f"  {key}={value}")
            
            # Show hosts
            if hasattr(task, 'hosts') and task.hosts:
                print(f"Hosts: {', '.join(task.hosts)}")
            
            return 0
            
        except Exception as e:
            print(format_exception_for_user(e), file=sys.stderr)
            return 1
    
    def _show_general_help(self) -> int:
        """Show general help information."""
        help_text = """
pf - A powerful task runner and automation tool

Usage:
  pf [options] <command> [args...]
  pf [options] run <task> [task_args...]

Commands:
  list                    List all available tasks
  run <task>             Run a specific task
  help [task]            Show help (optionally for a specific task)
  prune                  Clean up containers and resources
  debug-on               Enable debug mode
  debug-off              Disable debug mode

Options:
  -f, --file FILE        Use specific Pfyfile (default: Pfyfile.pf)
  -h, --hosts HOSTS      Override target hosts
  -e, --env KEY=VALUE    Set environment variables
  --debug                Enable debug output
  --dry-run              Show what would be executed without running
  --parallel             Run tasks in parallel when possible

Examples:
  pf list                List all tasks
  pf run build           Run the 'build' task
  pf run deploy --hosts prod1,prod2
  pf help deploy         Show help for 'deploy' task

For more information, see the documentation or visit the project repository.
"""
        print(help_text.strip())
        return 0