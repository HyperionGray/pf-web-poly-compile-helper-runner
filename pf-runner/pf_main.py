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
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing pf functionality
from pf_parser import (
    get_alias_map,
    _load_pfy_source_with_includes,
    parse_pfyfile_text,
    Task,
    list_dsl_tasks_with_desc,
    _merge_env_hosts,
    _normalize_hosts,
    _parse_host,
    _c_for,
    _dedupe_preserve_order,
    _interpolate,
    _exec_line_fabric,
    BUILTINS,
)
from pf_args import PfArgumentParser
from pf_exceptions import PFException, PFExecutionError, format_exception_for_user

# Import specialized components
from pf_subcommand_manager import SubcommandManager
from pf_builtin_commands import BuiltinCommandHandler
from pf_task_executor import TaskExecutor
from pf_shell import execute_shell_command
from pfuck import PfAutocorrect


class PfRunner:
    """Enhanced pf runner with subcommand support and modular architecture."""
    
    def __init__(self):
        self.arg_parser = PfArgumentParser()
        self.subcommand_manager = SubcommandManager()
        self.builtin_handler = BuiltinCommandHandler()
        self.task_executor = TaskExecutor()
        self.autocorrect = None
        
    def discover_subcommands(self, pfyfile: Optional[str] = None) -> Dict[str, List[str]]:
        """Discover subcommands from included files."""
        subcommands = {}
        
        try:
            # Load the main pfy source with includes
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfyfile)
            
            # Parse to find include statements and their tasks
            include_files = self._extract_include_files(dsl_src)
            
            for include_file in include_files:
                try:
                    # Load the included file
                    include_src = self._load_include_file(include_file, pfyfile)
                    include_tasks = parse_pfyfile_text(include_src, {})
                    
                    # Extract task names
                    task_names = list(include_tasks.keys())
                    
                    # Add subcommand to parser
                    self.arg_parser.add_subcommand_from_file(include_file, task_names)
                    
                    # Store for reference
                    subcommands[include_file] = task_names
                    
                except FileNotFoundError as e:
                    # Warn about missing include files
                    print(f"Warning: Include file not found: {include_file}", file=sys.stderr)
                except Exception as e:
                    # Warn about other errors but don't fail
                    print(f"Warning: Could not process include file {include_file}: {e}", file=sys.stderr)
                    
        except FileNotFoundError:
            # If the main Pfyfile is not found, that's expected in some cases
            # (e.g., using always-available tasks only), so don't warn
            pass
        except Exception as e:
            # Only warn for unexpected errors during discovery
            # This shouldn't prevent the tool from working
            print(f"Warning: Could not discover subcommands: {e}", file=sys.stderr)
            
        return subcommands
    
    def _extract_include_files(self, dsl_src: str) -> List[str]:
        """Extract include file paths from DSL source."""
        include_files = []
        
        for line in dsl_src.splitlines():
            line = line.strip()
            if line.startswith('include ') and not line.startswith('# '):
                try:
                    parts = shlex.split(line)
                    if len(parts) >= 2:
                        include_files.append(parts[1])
                except ValueError:
                    # Fallback to simple split if shlex fails
                    parts = line.split()
                    if len(parts) >= 2:
                        include_files.append(parts[1])
                        
        return include_files
    
    def _load_include_file(self, include_path: str, base_pfyfile: Optional[str] = None) -> str:
        """Load an include file."""
        if os.path.isabs(include_path):
            full_path = include_path
        else:
            if base_pfyfile:
                base_dir = os.path.dirname(os.path.abspath(base_pfyfile))
            else:
                pfy_resolved = _find_pfyfile()
                base_dir = os.path.dirname(os.path.abspath(pfy_resolved))
            full_path = os.path.join(base_dir, include_path)
            
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def run_command(self, args: List[str]) -> int:
        """Run pf command with enhanced argument parsing and error handling."""
        # Lightweight version flag handling to avoid mis-parsing as a task
        if args and args[0] in ("--version", "-V", "version"):
            try:
                from pf_grammar import __version__ as grammar_version
            except Exception:
                grammar_version = "unknown"
            print(f"pf (merged build) - grammar {grammar_version}")
            return 0

        # Discover subcommands first
        self.discover_subcommands()
        
        # Check if we need to resolve an alias
        # First, extract file argument if present (before any command)
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
        
        # Parse arguments
        try:
            # Discover subcommands first
            self.discover_subcommands()
            
            # Parse arguments
            try:
                parsed_args = self.arg_parser.parse_args(args)
            except SystemExit as e:
                return e.code if e.code is not None else 1
                
            # Initialize autocorrect with the specified file
            self.autocorrect = PfAutocorrect(parsed_args.file)
            
            # Handle different commands
            if parsed_args.command == 'list':
                return self._handle_list_command(parsed_args)
            elif parsed_args.command == 'help':
                return self._handle_help_command(parsed_args)
            elif parsed_args.command == 'run':
                return self._handle_run_command(parsed_args)
            elif parsed_args.command == 'prune':
                return self._handle_prune_command(parsed_args)
            elif parsed_args.command == 'debug-on':
                return self._handle_debug_on_command(parsed_args)
            elif parsed_args.command == 'debug-off':
                return self._handle_debug_off_command(parsed_args)
            elif hasattr(parsed_args, 'subcommand_tasks'):
                # It's a subcommand
                return self._handle_subcommand(parsed_args)
            else:
                raise PFException(
                    message=f"Unknown command: {parsed_args.command}",
                    suggestion="Run 'pf help' to see available commands"
                )
                
        except PFException as e:
            # Our custom exceptions - show full context
            print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
            return 1
        except Exception as e:
            # Unexpected exceptions - show with context
            print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
            return 1
    
    def _handle_prune_command(self, args) -> int:
        """Handle the prune command for syntax checking."""
        try:
            from pf_prune import prune_tasks
            
            passed, failed, failed_tasks = prune_tasks(
                file_arg=args.file,
                dry_run=getattr(args, 'dry_run', True),
                verbose=getattr(args, 'verbose', False),
                output_file=getattr(args, 'output', 'pfail.fail.pf')
            )
            return 0 if failed == 0 else 1
            
        except Exception as e:
            print(f"Error during prune: {e}", file=sys.stderr)
            return 1
    
    def _handle_debug_on_command(self, args) -> int:
        """Handle the debug-on command."""
        try:
            from pf_prune import set_debug_mode
            set_debug_mode(True)
            return 0
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error enabling debug mode: {e}", file=sys.stderr)
            return 1
    
    def _handle_debug_off_command(self, args) -> int:
        """Handle the debug-off command."""
        try:
            from pf_prune import set_debug_mode
            set_debug_mode(False)
            return 0
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error disabling debug mode: {e}", file=sys.stderr)
            return 1
    
    def _handle_list_command(self, args) -> int:
        """Handle the list command."""
        try:
            tasks_with_desc = list_dsl_tasks_with_desc(file_arg=args.file)
            
            if args.subcommand:
                # Filter tasks by subcommand
                print(f"Tasks for {args.subcommand}:")
                # This would need more sophisticated filtering
                # For now, show all tasks
            else:
                print("Available tasks:")
                
            if not tasks_with_desc:
                print("  No tasks found.")
                if args.file:
                    print(f"\nNote: Using Pfyfile: {args.file}")
                    print("Check if the file exists and contains task definitions.")
                else:
                    print("\nNote: No Pfyfile.pf found in current directory or parent directories.")
                    print("Create a Pfyfile.pf or specify one with: pf -f <path> list")
                return 0
                
            # Group tasks by category if possible
            main_tasks = []
            categorized_tasks = {}
            
            for task_name, description, aliases in tasks_with_desc:
                # Simple categorization based on task name patterns
                if any(prefix in task_name for prefix in ['web-', 'build-', 'install-', 'test-']):
                    category = task_name.split('-')[0]
                    if category not in categorized_tasks:
                        categorized_tasks[category] = []
                    categorized_tasks[category].append((task_name, description, aliases))
                else:
                    main_tasks.append((task_name, description, aliases))
            
            # Display main tasks first
            if main_tasks:
                print("\nCore tasks:")
                for task_name, description, aliases in main_tasks:
                    desc_text = f" - {description}" if description else ""
                    alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
                    print(f"  {task_name}{desc_text}{alias_text}")
            
            # Display categorized tasks
            for category, tasks in sorted(categorized_tasks.items()):
                print(f"\n{category.title()} tasks:")
                for task_name, description, aliases in tasks:
                    desc_text = f" - {description}" if description else ""
                    alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
                    print(f"  {task_name}{desc_text}{alias_text}")
                    
            # Show usage hint
            print(f"\nUsage: pf run <task_name> [params...]")
            print(f"       pf help <task_name>  # Show help for specific task")
            
            return 0
            
        except FileNotFoundError as e:
            # Specific error for missing file
            print(f"Error: Pfyfile not found: {e}", file=sys.stderr)
            if args.file:
                print(f"The specified file '{args.file}' does not exist.", file=sys.stderr)
            else:
                print("No Pfyfile.pf found in current directory or parent directories.", file=sys.stderr)
            print("\nSuggestions:", file=sys.stderr)
            print("  - Create a Pfyfile.pf in your project directory", file=sys.stderr)
            print("  - Specify a file with: pf -f <path> list", file=sys.stderr)
            print("  - Check the PFY_FILE environment variable", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error listing tasks: {e}", file=sys.stderr)
            print("\nTraceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return 1
    
    def _handle_help_command(self, args) -> int:
        """Handle the help command."""
        if args.topic:
            # Show help for specific task or subcommand
            return self._show_task_help(args.topic, args.file)
        else:
            # Show general help
            self.arg_parser.parser.print_help()
            return 0
    
    def _show_task_help(self, task_name: str, pfyfile: Optional[str] = None) -> int:
        """Show help for a specific task."""
        try:
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfyfile)
            dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
            
            if task_name in dsl_tasks:
                task = dsl_tasks[task_name]
                print(f"Task: {task_name}")
                if task.description:
                    print(f"Description: {task.description}")
                print("\nCommands:")
                for line in task.lines:
                    print(f"  {line}")
            elif task_name in BUILTINS:
                print(f"Built-in task: {task_name}")
                print("Commands:")
                for line in BUILTINS[task_name]:
                    print(f"  {line}")
            else:
                # Try to suggest corrections
                suggestions = self.autocorrect.suggest_task_correction(task_name)
                print(f"Task '{task_name}' not found.")
                if suggestions:
                    print("Did you mean:")
                    for suggestion in suggestions:
                        print(f"  {suggestion}")
                return 1
                
            return 0
            
        except Exception as e:
            print(f"Error showing help for {task_name}: {e}", file=sys.stderr)
            return 1
    
    def _handle_run_command(self, args) -> int:
        """Handle the run command."""
        if not hasattr(args, 'tasks') or not args.tasks:
            print("No tasks specified to run.", file=sys.stderr)
            return 1
            
        return self._execute_tasks(args, args.tasks)
    
    def _handle_subcommand(self, args) -> int:
        """Handle a subcommand (from included file)."""
        if not hasattr(args, 'task'):
            print("No task specified for subcommand.", file=sys.stderr)
            return 1
            
        # Combine task name with parameters
        task_args = [args.task]
        if hasattr(args, 'params') and args.params:
            task_args.extend(args.params)
            
        return self._execute_tasks(args, task_args)
    
    def _execute_tasks(self, args, task_args: List[str]) -> int:
        """Execute the specified tasks."""
        try:
            # Build host list
            env_names = args.env or []
            host_specs = []
            
            if args.hosts:
                host_specs.extend(_normalize_hosts(args.hosts))
            if args.host:
                host_specs.extend(args.host)
                
            # Resolve hosts
            env_hosts = _merge_env_hosts(env_names)
            merged_hosts = _dedupe_preserve_order(env_hosts + host_specs)
            if not merged_hosts:
                merged_hosts = ["@local"]
            
            # Load tasks
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=args.file)
            dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
            valid_task_names = set(BUILTINS.keys()) | set(dsl_tasks.keys())
            
            # Parse task arguments
            selected_tasks = self._parse_task_arguments(task_args, valid_task_names, dsl_tasks)
            
            if not selected_tasks:
                print("No valid tasks found to execute.", file=sys.stderr)
                return 1
            
            # Execute tasks across hosts
            return self._execute_on_hosts(selected_tasks, merged_hosts, args)
            
        except Exception as e:
            print(f"Error executing tasks: {e}", file=sys.stderr)
            return 1
    
    def _parse_task_arguments(self, task_args: List[str], valid_task_names: set, dsl_tasks: Dict[str, Task]) -> List[Tuple[str, List[str], Dict[str, str]]]:
        """Parse task arguments into (task_name, lines, params) tuples."""
        selected = []
        i = 0
        
        while i < len(task_args):
            task_name = task_args[i]
            
            # Check if task exists
            if task_name not in valid_task_names:
                # Try autocorrect
                suggestions = self.autocorrect.suggest_task_correction(task_name)
                
                # Raise a proper exception instead of printing and returning
                available_tasks = list(valid_task_names)
                raise PFTaskNotFoundError(
                    task_name=task_name,
                    available_tasks=available_tasks,
                    suggestion=f"Did you mean: {', '.join(suggestions)}?" if suggestions else None
                )
            
            i += 1
            
            # Parse parameters for this task
            params = {}
            while i < len(task_args) and '=' in task_args[i] and not task_args[i].startswith('--'):
                key, value = task_args[i].split('=', 1)
                params[key] = value
                i += 1
            
            # Get task lines
            if task_name in BUILTINS:
                lines = BUILTINS[task_name]
            else:
                lines = dsl_tasks[task_name].lines
            
            selected.append((task_name, lines, params))
        
        return selected
    
    def _execute_on_hosts(self, selected_tasks: List[Tuple[str, List[str], Dict[str, str]]], 
                         hosts: List[str], args) -> int:
        """Execute tasks on the specified hosts."""
        
        def run_host(host_spec: str) -> int:
            """Run tasks on a single host."""
            spec = _parse_host(host_spec, default_user=args.user, default_port=args.port)
            prefix = f"[{host_spec}]"
            
            # Set up connection
            if spec.get("local"):
                connection = None
            else:
                connection_tuple = _c_for(spec, args.sudo, args.sudo_user)
                if isinstance(connection_tuple, tuple):
                    connection, sudo_flag, sudo_user = connection_tuple
                else:
                    connection = None
                    sudo_flag = args.sudo
                    sudo_user = args.sudo_user
                
                if connection is not None:
                    try:
                        connection.open()
                    except Exception as e:
                        raise PFConnectionError(
                            message=str(e),
                            host=host_spec,
                            suggestion="Verify SSH credentials and network connectivity"
                        )
            
            # Execute tasks
            rc = 0
            for task_name, lines, params in selected_tasks:
                print(f"{prefix} --> {task_name}")
                task_env = {}
                
                for line in lines:
                    stripped = line.strip()
                    
                    # Handle env command (stateful)
                    if stripped.startswith('env '):
                        for tok in shlex.split(stripped)[1:]:
                            if '=' in tok:
                                k, v = tok.split('=', 1)
                                task_env[k] = _interpolate(v, params, task_env)
                        continue
                    
                    try:
                        # Use enhanced shell execution for shell commands
                        if stripped.startswith('shell '):
                            shell_cmd = stripped[6:].strip()  # Remove 'shell ' prefix
                            shell_cmd = _interpolate(shell_cmd, params, task_env)
                            
                            rc = execute_shell_command(
                                shell_cmd, task_env, args.sudo, args.sudo_user,
                                connection, prefix
                            )
                        else:
                            # Use original execution for other commands
                            rc = _exec_line_fabric(
                                line, connection, task_env, task_name,
                                args.sudo, args.sudo_user
                            )
                        
                        if rc != 0:
                            # Command failed - create detailed error
                            raise PFExecutionError(
                                message=f"Command failed with exit code {rc}",
                                task_name=task_name,
                                command=line,
                                exit_code=rc,
                                environment=task_env,
                                suggestion="Check the command output above for details"
                            )
                            
                    except PFExecutionError:
                        # Re-raise our exceptions
                        raise
                    except Exception as e:
                        # Wrap unexpected errors
                        raise PFExecutionError(
                            message=f"Unexpected error executing command: {e}",
                            task_name=task_name,
                            command=line,
                            environment=task_env
                        )
            
            # Clean up connection
            if connection is not None:
                connection.close()
                
            return rc
        
        # Execute in parallel across hosts
        rc_total = 0
        with ThreadPoolExecutor(max_workers=min(32, len(hosts))) as executor:
            futures = {executor.submit(run_host, host): host for host in hosts}
            
            for future in as_completed(futures):
                host = futures[future]
                try:
                    rc = future.result()
                except PFException as e:
                    # Show formatted error for PF exceptions
                    print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
                    rc = 1
                except Exception as e:
                    # Wrap and show unexpected exceptions
                    print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
                    rc = 1
                rc_total = rc_total or rc
        
        return rc_total


def main(argv: List[str]) -> int:
    """Main entry point for enhanced pf."""
    runner = PfRunner()
    return runner.run_command(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
