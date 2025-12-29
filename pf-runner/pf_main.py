#!/usr/bin/env python3
"""
pf_main.py - Enhanced main entry point for pf with subcommand support

This module provides:
- Integration of enhanced argument parsing
- Orchestration of specialized components
- Backward compatibility with existing usage
- Integration with pfuck autocorrect

Architecture:
  This module now acts as a lightweight orchestrator, delegating to specialized components:
  - SubcommandManager: Handles subcommand discovery and registration
  - BuiltinCommandHandler: Manages built-in command implementations
  - TaskExecutor: Orchestrates task execution and parallel processing
  - pf_parser: Core DSL parsing and task management
  - pf_args: Argument parsing
  - pf_shell: Shell command execution
  - pfuck: Autocorrect functionality

The refactoring follows Single Responsibility Principle by separating concerns
into focused, cohesive components while maintaining the same public interface.
"""

import os
import sys
import traceback
from typing import List, Dict, Optional

# Import existing pf functionality
from pf_parser import get_alias_map
from pf_args import PfArgumentParser
from pf_exceptions import PFException, format_exception_for_user

# Import specialized components
from pf_subcommand_manager import SubcommandManager
from pf_builtin_commands import BuiltinCommandHandler
from pf_task_executor import TaskExecutor


class PfRunner:
    """Enhanced pf runner with subcommand support and modular architecture."""
    
    def __init__(self):
        self.arg_parser = PfArgumentParser()
        self.subcommand_manager = SubcommandManager()
        self.builtin_handler = BuiltinCommandHandler()
        self.task_executor = TaskExecutor()
        self.autocorrect = None
    
    def run_command(self, args: List[str]) -> int:
        """Run pf command with enhanced argument parsing and error handling."""
        
        # Discover and register subcommands
        self.subcommand_manager.register_subcommands_with_parser(self.arg_parser)
        
        # Handle alias resolution
        args = self._resolve_aliases(args)
        
        # Parse arguments
        try:
            parsed_args = self.arg_parser.parse_args(args)
        except SystemExit as e:
            return e.code if e.code is not None else 1
        
        # Route to appropriate handler
        try:
            return self._route_command(parsed_args)
        except PFException as e:
            print(format_exception_for_user(e), file=sys.stderr)
            return 1
        except Exception as e:
            # Try autocorrect for unexpected errors
            if self._try_autocorrect(args, e):
                return 0
            
            print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
            return 1
    
    def _resolve_aliases(self, args: List[str]) -> List[str]:
        """Resolve command aliases to actual task names."""
        # Extract file argument if present (before any command)
        file_arg = None
        args_copy = list(args)
        i = 0
        while i < len(args_copy):
            if args_copy[i] in ('-f', '--file') and i + 1 < len(args_copy):
                file_arg = args_copy[i + 1]
                i += 2
            elif args_copy[i].startswith('--file='):
                file_arg = args_copy[i].split('=', 1)[1]
                i += 1
            elif not args_copy[i].startswith('-'):
                # Found a non-option argument, check if it's an alias
                builtins = {'list', 'help', 'run', 'prune', 'debug-on', 'debug-off'}
                if args_copy[i] not in builtins:
                    try:
                        alias_map = get_alias_map(file_arg=file_arg)
                        if args_copy[i] in alias_map:
                            # Replace alias with actual task name and prefix with 'run'
                            task_name = alias_map[args_copy[i]]
                            args = args[:i] + ['run', task_name] + args[i+1:]
                    except Exception:
                        # If alias resolution fails, continue with normal parsing
                        pass
                break
            else:
                i += 1
        
        return args
    
    def _route_command(self, args) -> int:
        """Route parsed arguments to the appropriate command handler."""
        command = getattr(args, 'command', None)
        
        if command == 'prune':
            return self.builtin_handler.handle_prune_command(args)
        elif command == 'debug-on':
            return self.builtin_handler.handle_debug_on_command(args)
        elif command == 'debug-off':
            return self.builtin_handler.handle_debug_off_command(args)
        elif command == 'list':
            return self.builtin_handler.handle_list_command(args)
        elif command == 'help':
            return self.builtin_handler.handle_help_command(args)
        elif command == 'run':
            return self.task_executor.handle_run_command(args)
        elif hasattr(args, 'subcommand'):
            return self.task_executor.handle_subcommand(args)
        else:
            print("No command specified. Use 'pf help' for usage information.", file=sys.stderr)
            return 1
    
    def _try_autocorrect(self, args: List[str], error: Exception) -> bool:
        """Try to autocorrect the command if pfuck is available."""
        try:
            # Lazy import pfuck to avoid circular dependencies
            if self.autocorrect is None:
                try:
                    from pfuck import PfuckAutocorrect
                    self.autocorrect = PfuckAutocorrect()
                except ImportError:
                    return False
            
            # Try to get a correction
            correction = self.autocorrect.suggest_correction(args, str(error))
            if correction:
                print(f"Did you mean: {correction}", file=sys.stderr)
                # Could potentially auto-execute the correction here
                return True
                
        except Exception:
            # If autocorrect fails, don't let it break the main error handling
            pass
        
        return False


def main(argv: List[str]) -> int:
    """Main entry point for enhanced pf."""
    runner = PfRunner()
    return runner.run_command(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))