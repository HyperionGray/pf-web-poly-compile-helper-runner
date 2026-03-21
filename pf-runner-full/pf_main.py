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
import json
import atexit
import shutil
import tempfile
import traceback
import difflib
import shlex
import textwrap
import re
from typing import Any, List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Prefer bundled vendor deps (for .deb installs) before falling back to site-packages.
VENDOR_PATH = Path(__file__).resolve().parent / "vendor"
if VENDOR_PATH.exists():
    sys.path.insert(0, str(VENDOR_PATH))

# Import existing pf functionality
from pf_parser import (
    get_alias_map,
    _find_pfyfile,
    _resolve_pfyfile_reference,
    _load_pfy_source_with_includes,
    parse_pfyfile_text,
    Task,
    _merge_env_hosts,
    _normalize_hosts,
    _parse_host,
    _c_for,
    _dedupe_preserve_order,
    _interpolate,
    _parse_heredoc_syntax,
    _parse_lang_bracket,
    _canonical_lang,
    _render_polyglot_command,
    _exec_line_fabric,
    BUILTINS,
)
from pf_args import PfArgumentParser
from pf_exceptions import (
    PFException,
    PFExecutionError,
    PFTaskNotFoundError,
    PFConnectionError,
    format_exception_for_user,
)

# Import specialized components
from pf_subcommand_manager import SubcommandManager
from pf_builtin_commands import BuiltinCommandHandler
from pf_task_executor import TaskExecutor
from pf_shell import execute_shell_command
from pfuck import PfAutocorrect

# (task_name, description, aliases)
TaskListing = Tuple[str, Optional[str], List[str]]
_PFYFILE_MODULE_PREFIX = "Pfyfile."
_PFYFILE_MODULE_SUFFIX = ".pf"


class PfRunner:
    """Enhanced pf runner with subcommand support and modular architecture."""
    
    def __init__(self):
        self.arg_parser = PfArgumentParser()
        self.subcommand_manager = SubcommandManager()
        self.builtin_handler = BuiltinCommandHandler()
        self.task_executor = TaskExecutor()
        self.autocorrect = None

    def discover_subcommands(self, pfyfile: Optional[str] = None) -> Dict[str, List[str]]:
        """Discover and register subcommands from included files."""
        self.subcommand_manager.register_subcommands_with_parser(self.arg_parser, pfyfile)
        return self.subcommand_manager.discover_subcommands(pfyfile)

    def _extract_global_env(self, dsl_src: str) -> Dict[str, str]:
        """Extract env KEY=VAL declarations outside task blocks."""
        global_env: Dict[str, str] = {}
        in_task = False

        for raw_line in dsl_src.splitlines():
            stripped = raw_line.strip()

            if stripped.startswith("task "):
                in_task = True
                continue
            if in_task and stripped == "end":
                in_task = False
                continue

            if in_task:
                continue

            if stripped.startswith("env "):
                for tok in shlex.split(stripped)[1:]:
                    if "=" in tok:
                        k, v = tok.split("=", 1)
                        global_env[k] = _interpolate(v, {}, global_env)

        return global_env

    def _module_name_from_source_file(self, source_file: Optional[str]) -> Optional[str]:
        """Convert a `Pfyfile.<name>.pf` path into its module/subcommand name.

        Underscores are normalized to hyphens and the result is lowercased.
        Returns None for missing paths, non-matching filenames, or the main
        `Pfyfile.pf`, which does not map to a module subcommand.
        """
        if not source_file:
            return None

        basename = os.path.basename(source_file)
        if not (
            basename.startswith(_PFYFILE_MODULE_PREFIX)
            and basename.endswith(_PFYFILE_MODULE_SUFFIX)
        ):
            return None

        module_name = basename[
            len(_PFYFILE_MODULE_PREFIX) : -len(_PFYFILE_MODULE_SUFFIX)
        ].replace("_", "-").lower()
        # The main Pfyfile maps to direct tasks, not a nested module/subcommand.
        if module_name in ("", "pf"):
            return None
        return module_name

    def _format_task_count(self, task_count: int) -> str:
        """Format a human-readable task count."""
        noun = "task" if task_count == 1 else "tasks"
        return f"{task_count} {noun}"

    # Module names that are always flattened into the root listing surface.
    _ROOT_FLAT_MODULES = frozenset({"always-available", "module-compat"})

    def _load_task_listing(
        self, file_arg: Optional[str]
    ) -> Tuple[List[TaskListing], Dict[str, List[TaskListing]]]:
        """Load task metadata as `(direct_tasks, module_tasks)`.

        Each task entry is `(task_name, description, aliases)`. `direct_tasks`
        are tasks defined in the main Pfyfile, while `module_tasks` is keyed by
        module name and contains tasks sourced from included `Pfyfile.<name>.pf`
        files.

        Special flattening rules applied here:
        - Tasks from the same-named included file (e.g., ``web-testing/Pfyfile.web.pf``
          when viewing the ``web`` module) are merged into ``direct_tasks``.
        - Tasks from ``always-available`` and ``module-compat`` are merged into
          ``direct_tasks`` when loading the root/default Pfyfile surface.
        """
        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
        dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)

        resolved_pfyfile = _find_pfyfile(file_arg=file_arg)
        main_pfyfile = (
            os.path.abspath(resolved_pfyfile) if resolved_pfyfile and os.path.exists(resolved_pfyfile) else None
        )

        # Derive module name for the main Pfyfile (None for root Pfyfile.pf).
        main_module_name = self._module_name_from_source_file(main_pfyfile) if main_pfyfile else None
        is_root = main_module_name is None

        direct_tasks: List[TaskListing] = []
        module_tasks: Dict[str, List[TaskListing]] = {}

        for task_name, task in sorted(dsl_tasks.items()):
            task_info = (task_name, task.description, task.aliases)
            source_file = os.path.abspath(task.source_file) if task.source_file else None

            if main_pfyfile and source_file == main_pfyfile:
                direct_tasks.append(task_info)
                continue

            module_name = self._module_name_from_source_file(source_file)
            if module_name:
                # Same-named included file: merge into the core surface.
                if main_module_name and module_name == main_module_name:
                    direct_tasks.append(task_info)
                # Root-surface flat modules: merge into root core tasks.
                elif is_root and module_name in self._ROOT_FLAT_MODULES:
                    direct_tasks.append(task_info)
                else:
                    module_tasks.setdefault(module_name, []).append(task_info)
            else:
                direct_tasks.append(task_info)

        return direct_tasks, module_tasks

    def _print_task_entries(self, tasks: List[TaskListing]) -> None:
        """Print `(task_name, description, aliases)` entries as CLI list rows."""
        for task_name, description, aliases in tasks:
            desc_text = f" - {description}" if description else ""
            alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
            print(f"  {task_name}{desc_text}{alias_text}")

    def _task_entry_to_dict(self, task: TaskListing) -> Dict[str, Any]:
        """Serialize `(task_name, description, aliases)` for JSON output."""
        task_name, description, aliases = task
        return {
            "name": task_name,
            "description": description,
            "aliases": aliases,
        }
    
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

        # Register subcommands before argparse parsing (uses `-f/--file` if provided).
        self.discover_subcommands(pfyfile=file_arg)
        
        # Parse arguments
        try:
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
            elif parsed_args.command == 'version':
                return self._handle_version_command(parsed_args)
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

    def _handle_version_command(self, args) -> int:
        """Display version information."""
        version = getattr(self.arg_parser, "version", None) or "unknown"
        grammar_version = getattr(sys.modules.get("pf_grammar"), "__version__", None)

        print(f"pf {version}")
        if grammar_version:
            print(f"pf grammar {grammar_version}")

        install_dir = Path(__file__).resolve().parent
        print(f"install: {install_dir}")
        return 0
    
    def _handle_list_command(self, args) -> int:
        """Handle the list command."""
        file_arg = args.file
        try:
            target = getattr(args, "target", None)
            if target and not file_arg:
                resolved = _resolve_pfyfile_reference(target, start_dir=os.getcwd())
                file_arg = resolved or target

            direct_tasks, module_tasks = self._load_task_listing(file_arg)
            requested_module = (getattr(args, "subcommand", None) or "").strip().lower()
            output_json = bool(getattr(args, "json", False))

            if requested_module:
                tasks = module_tasks.get(requested_module, [])
                if not tasks:
                    if output_json:
                        print(
                            json.dumps(
                                {
                                    "error": f"No tasks found for module '{requested_module}'.",
                                    "requested_module": requested_module,
                                    "available_modules": sorted(module_tasks),
                                    "source": file_arg,
                                },
                                indent=2,
                                sort_keys=True,
                            )
                        )
                        return 1
                    print(f"No tasks found for module '{args.subcommand}'.", file=sys.stderr)
                    if module_tasks:
                        available_modules = ", ".join(sorted(module_tasks))
                        print(f"Available modules: {available_modules}", file=sys.stderr)
                    return 1

                if output_json:
                    print(
                        json.dumps(
                            {
                                "requested_module": requested_module,
                                "source": file_arg,
                                "task_count": len(tasks),
                                "tasks": [self._task_entry_to_dict(task) for task in tasks],
                            },
                            indent=2,
                            sort_keys=True,
                        )
                    )
                    return 0

                print(f"Tasks for {requested_module}:")
                self._print_task_entries(tasks)
                print(f"\nUsage: pf {requested_module} <task_name> [params...]")
                print("       pf help <task_name>  # Show help for a specific task")
                return 0

            total_tasks = len(direct_tasks) + sum(len(tasks) for tasks in module_tasks.values())
            if output_json:
                module_task_count = sum(len(tasks) for tasks in module_tasks.values())
                print(
                    json.dumps(
                        {
                            "source": file_arg,
                            "core_tasks": [self._task_entry_to_dict(task) for task in direct_tasks],
                            "modules": {
                                module_name: [
                                    self._task_entry_to_dict(task) for task in tasks
                                ]
                                for module_name, tasks in sorted(module_tasks.items())
                            },
                            "summary": {
                                "core_task_count": len(direct_tasks),
                                "module_count": len(module_tasks),
                                "module_task_count": module_task_count,
                                "total_task_count": total_tasks,
                            },
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0

            print("Available tasks:")
            if total_tasks == 0:
                print("  No tasks found.")
                if file_arg:
                    print(f"\nNote: Using Pfyfile: {file_arg}")
                    print("Check if the file exists and contains task definitions.")
                else:
                    print("\nNote: No Pfyfile found in current directory or parent directories.")
                    print(
                        "Create pf-files/Pfyfile.pf (recommended) or Pfyfile.pf, or specify one with: pf -f <path> list"
                    )
                return 0

            if direct_tasks:
                print("\nCore tasks:")
                self._print_task_entries(direct_tasks)

            if module_tasks:
                print("\nModules:")
                for module_name, tasks in sorted(module_tasks.items()):
                    print(f"  {module_name} ({self._format_task_count(len(tasks))})")

            print("\nUsage:")
            print("  pf <task_name> [params...]")
            print("  pf <module|file.pf>                # List tasks from a module/file")
            print("  pf <module|file.pf> <task_name> [params...]")
            print("  pf help <task_name>                # Show help for a specific task")

            return 0
        except FileNotFoundError as e:
            # Specific error for missing file
            print(f"Error: Pfyfile not found: {e}", file=sys.stderr)
            if file_arg:
                print(f"The specified file '{file_arg}' does not exist.", file=sys.stderr)
            else:
                print("No Pfyfile found in current directory or parent directories.", file=sys.stderr)
            print("\nSuggestions:", file=sys.stderr)
            print(
                "  - Create pf-files/Pfyfile.pf (recommended) or Pfyfile.pf in your project directory",
                file=sys.stderr,
            )
            print("  - Specify a file with: pf -f <path> list", file=sys.stderr)
            print("  - Check the PFY_FILE environment variable", file=sys.stderr)
            return 1
        except BrokenPipeError:
            # Output pipe closed (e.g., piped to head); exit quietly
            try:
                sys.stdout.close()
            except Exception:
                pass
            return 0
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
                module_name = task_name.strip().lower()
                _direct_tasks, module_tasks = self._load_task_listing(pfyfile)
                if module_name in module_tasks:
                    print(f"Tasks for {module_name}:")
                    self._print_task_entries(module_tasks[module_name])
                    print(f"\nUsage: pf {module_name} <task_name> [params...]")
                    return 0
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
        task_args = list(getattr(args, 'tasks', []) or [])
        if not hasattr(args, 'tasks') or not task_args:
            print("No tasks specified to run.", file=sys.stderr)
            return 1

        if not args.file and task_args:
            resolved = _resolve_pfyfile_reference(task_args[0], start_dir=os.getcwd())
            if resolved:
                args.file = resolved
                task_args = task_args[1:]

        if not task_args:
            setattr(args, "target", None)
            setattr(args, "subcommand", None)
            return self._handle_list_command(args)
            
        return self._execute_tasks(args, task_args)
    
    def _handle_subcommand(self, args) -> int:
        """Handle a subcommand (from included file)."""
        if not hasattr(args, 'task'):
            print("No task specified for subcommand.", file=sys.stderr)
            return 1
        allowed_tasks = set(getattr(args, "subcommand_tasks", []) or [])
        if allowed_tasks and args.task not in allowed_tasks:
            available = ", ".join(sorted(allowed_tasks))
            print(
                f"Task '{args.task}' is not available in module '{args.command}'.",
                file=sys.stderr,
            )
            if available:
                print(f"Available tasks: {available}", file=sys.stderr)
            return 1

        scoped_file = getattr(args, "subcommand_file", None)
        if scoped_file:
            args.file = scoped_file
            
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
            global_env = self._extract_global_env(dsl_src)
            # Ensure nested `pf ...` calls inside tasks resolve to this runner (not an
            # unrelated `pf` earlier in PATH).
            if "PATH" not in global_env:
                shim_dir = tempfile.mkdtemp(prefix="pf-self-")
                pf_shim = Path(shim_dir) / "pf"
                pf_shim.write_text(
                    "#!/usr/bin/env bash\n"
                    f"exec {shlex.quote(sys.executable)} {shlex.quote(os.path.abspath(__file__))} \"$@\"\n",
                    encoding="utf-8",
                )
                pf_shim.chmod(0o755)
                atexit.register(shutil.rmtree, shim_dir, ignore_errors=True)
                existing_path = os.environ.get("PATH", "")
                global_env["PATH"] = f"{shim_dir}:{existing_path}" if existing_path else shim_dir
            dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
            valid_task_names = set(BUILTINS.keys()) | set(dsl_tasks.keys())
            
            # Parse task arguments
            selected_tasks = self._parse_task_arguments(task_args, valid_task_names, dsl_tasks)
            
            if not selected_tasks:
                print("No valid tasks found to execute.", file=sys.stderr)
                return 1
            
            # Execute tasks across hosts
            return self._execute_on_hosts(selected_tasks, merged_hosts, args, global_env)
            
        except Exception as e:
            print(f"Error executing tasks: {e}", file=sys.stderr)
            return 1
    
    def _parse_task_arguments(
        self,
        task_args: List[str],
        valid_task_names: set,
        dsl_tasks: Dict[str, Task],
    ) -> List[Tuple[str, List[str], Dict[str, str], Optional[str]]]:
        """Parse task arguments into (task_name, lines, params, default_lang) tuples."""
        selected = []
        i = 0
        task_name_lookup = self._build_task_name_lookup(valid_task_names)
        
        while i < len(task_args):
            resolved_name, consumed_tokens = self._consume_task_name_tokens(
                task_args,
                i,
                valid_task_names,
                task_name_lookup,
            )
            i += consumed_tokens

            task_defaults: Dict[str, str] = {}
            if resolved_name not in BUILTINS:
                task_defaults = dict(dsl_tasks[resolved_name].params)
            
            # Parse parameters for this task
            cli_params: Dict[str, str] = {}
            while i < len(task_args):
                tok = task_args[i]

                # Stop if the next token looks like a new task name
                if self._find_task_name_match(tok, task_name_lookup):
                    break

                # --key=value
                if tok.startswith('--') and '=' in tok:
                    key, value = tok[2:].split('=', 1)
                    cli_params[key] = value
                    i += 1
                    continue

                # --key value (treat lone --key as boolean true)
                if tok.startswith('--'):
                    key = tok[2:]
                    next_tok = task_args[i + 1] if (i + 1) < len(task_args) else None
                    should_consume_next = (
                        next_tok is not None
                        and not next_tok.startswith('--')
                        and (
                            key in task_defaults
                            or (
                                '=' not in next_tok
                                and self._find_task_name_match(next_tok, task_name_lookup) is None
                            )
                        )
                    )
                    if should_consume_next:
                        value = task_args[i + 1]
                        i += 2
                    else:
                        value = "true"
                        i += 1
                    cli_params[key] = value
                    continue

                # key=value
                if '=' in tok:
                    key, value = tok.split('=', 1)
                    cli_params[key] = value
                    i += 1
                    continue

                # Anything else likely begins the next task
                break
            
            # Get task lines
            if resolved_name in BUILTINS:
                lines = BUILTINS[resolved_name]
                default_lang = None
                merged_params: Dict[str, str] = dict(cli_params)
            else:
                task = dsl_tasks[resolved_name]
                lines = task.lines
                default_lang = task.default_lang
                merged_params = dict(task.params)
                merged_params.update(cli_params)
            
            selected.append((resolved_name, lines, merged_params, default_lang))
        
        return selected

    def _normalize_task_name_key(self, task_name: str) -> str:
        """Normalize task names so spaces, underscores, and hyphens compare equivalently."""
        lowered = task_name.strip().lower().replace("_", "-")
        return re.sub(r"-+", "-", re.sub(r"\s+", "-", lowered)).strip("-")

    def _build_task_name_lookup(self, valid_task_names: set) -> Dict[str, str]:
        """Build a best-effort lookup for exact and normalized task names."""
        lookup: Dict[str, str] = {}
        ambiguous: set[str] = set()

        for name in valid_task_names:
            for key in {name, name.lower(), self._normalize_task_name_key(name)}:
                if not key:
                    continue
                existing = lookup.get(key)
                if existing is None:
                    lookup[key] = name
                elif existing != name:
                    ambiguous.add(key)

        for key in ambiguous:
            lookup.pop(key, None)

        return lookup

    def _find_task_name_match(
        self,
        task_name: str,
        task_name_lookup: Dict[str, str],
    ) -> Optional[str]:
        """Resolve exact/normalized task names without invoking fuzzy autocorrect."""
        if task_name in task_name_lookup:
            return task_name_lookup[task_name]
        lowered = task_name.lower()
        if lowered in task_name_lookup:
            return task_name_lookup[lowered]
        normalized = self._normalize_task_name_key(task_name)
        if normalized in task_name_lookup:
            return task_name_lookup[normalized]
        return None

    def _looks_like_param_token(self, token: str) -> bool:
        """Return True when a token is clearly a CLI parameter instead of a task token."""
        return token.startswith("--") or "=" in token

    def _consume_task_name_tokens(
        self,
        task_args: List[str],
        start_idx: int,
        valid_task_names: set,
        task_name_lookup: Dict[str, str],
    ) -> Tuple[str, int]:
        """
        Resolve one task reference from the task-argument stream.

        Supports compatibility forms like `pf this task` for `this-task` while
        preserving plain multi-task syntax when the next token is clearly another task.
        """
        first_token = task_args[start_idx]
        exact_single = self._find_task_name_match(first_token, task_name_lookup)

        max_end = start_idx + 1
        while max_end < len(task_args) and not self._looks_like_param_token(task_args[max_end]):
            max_end += 1

        best_multi_match: Optional[str] = None
        best_multi_len = 0
        for end_idx in range(max_end, start_idx + 1, -1):
            if (end_idx - start_idx) < 2:
                continue
            candidate = " ".join(task_args[start_idx:end_idx])
            resolved = self._find_task_name_match(candidate, task_name_lookup)
            if resolved:
                best_multi_match = resolved
                best_multi_len = end_idx - start_idx
                break

        next_token_can_be_task = (
            (start_idx + 1) < len(task_args)
            and not self._looks_like_param_token(task_args[start_idx + 1])
            and self._find_task_name_match(task_args[start_idx + 1], task_name_lookup) is not None
        )

        if best_multi_match and (exact_single is None or not next_token_can_be_task):
            return best_multi_match, best_multi_len

        if exact_single:
            return exact_single, 1

        if best_multi_match:
            return best_multi_match, best_multi_len

        return self._resolve_task_name(first_token, valid_task_names, task_name_lookup), 1

    def _resolve_task_name(
        self,
        task_name: str,
        valid_task_names: set,
        task_name_lookup: Optional[Dict[str, str]] = None,
    ) -> str:
        """Return a valid task name, applying autocorrect with user-controlled policy."""
        task_name_lookup = task_name_lookup or self._build_task_name_lookup(valid_task_names)
        matched = self._find_task_name_match(task_name, task_name_lookup)
        if matched:
            return matched

        mode = os.getenv("PF_AUTOCORRECT_MODE", "auto").lower()
        threshold = float(os.getenv("PF_AUTOCORRECT_THRESHOLD", "0.75"))

        close_matches = difflib.get_close_matches(task_name, valid_task_names, n=5, cutoff=0.4)
        auto_suggestions = self.autocorrect.suggest_task_correction(task_name)

        # Merge suggestions while preserving order
        suggestions = []
        seen = set()
        for s in close_matches + auto_suggestions:
            if s not in seen:
                seen.add(s)
                suggestions.append(s)

        best = suggestions[0] if suggestions else None
        score = difflib.SequenceMatcher(None, task_name, best or "").ratio() if best else 0.0

        def _fail():
            raise PFTaskNotFoundError(
                task_name=task_name,
                available_tasks=list(valid_task_names),
                suggestion=f"Did you mean: {', '.join(suggestions)}?" if suggestions else None
            )

        if mode == "off":
            _fail()

        if mode == "ask":
            if best and score >= 0.6 and sys.stdin.isatty():
                reply = input(
                    f"Task '{task_name}' not found. Run '{best}' instead? [Y/n]: "
                ).strip().lower()
                if reply in ("", "y", "yes"):
                    print(
                        f"Auto-correcting '{task_name}' -> '{best}' (confidence {score:.2f})",
                        file=sys.stderr,
                    )
                    return best
                _fail()
            _fail()

        # default: auto (warn)
        if best and score >= threshold:
            print(
                f"Warning: task '{task_name}' not found. Auto-corrected to '{best}' "
                f"(confidence {score:.2f}). Set PF_AUTOCORRECT_MODE=off to disable.",
                file=sys.stderr,
            )
            return best

        _fail()
    
    def _execute_on_hosts(
        self,
        selected_tasks: List[Tuple[str, List[str], Dict[str, str], Optional[str]]],
        hosts: List[str],
        args,
        global_env: Dict[str, str],
    ) -> int:
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
            for task_name, lines, params, task_default_lang in selected_tasks:
                print(f"{prefix} --> {task_name}")
                task_env = dict(global_env)
                # Expose task parameters as environment variables so heredoc blocks
                # (which are not interpolated) can still read them.
                task_env.update(params)
                implicit_lang: Optional[str] = task_default_lang or params.get("default_lang")
                shell_lang: Optional[str] = None
                shell_lang_cleared = False
                pending_script: List[str] = []

                def active_lang(line_lang: Optional[str] = None) -> Optional[str]:
                    if line_lang:
                        return line_lang
                    if shell_lang:
                        return shell_lang
                    if shell_lang_cleared:
                        return None
                    return implicit_lang

                def flush_pending() -> None:
                    nonlocal rc, pending_script, implicit_lang
                    if not pending_script:
                        return
                    script_body = textwrap.dedent("\n".join(pending_script)).strip("\n")
                    lang_for_pending = active_lang()
                    if not lang_for_pending:
                        raise PFExecutionError(
                            message="Inline code block provided without default_lang/shell_lang",
                            task_name=task_name,
                            command=script_body,
                            environment=task_env,
                            suggestion="Add shell_lang <lang> or default_lang <lang> before inline code",
                        )
                    rendered_cmd, _lang = _render_polyglot_command(
                        lang_for_pending, script_body, os.getcwd()
                    )
                    rc_flush = _exec_line_fabric(
                        rendered_cmd, connection, task_env, task_name,
                        args.sudo, args.sudo_user
                    )
                    if rc_flush != 0:
                        raise PFExecutionError(
                            message=f"Command failed with exit code {rc_flush}",
                            task_name=task_name,
                            command=rendered_cmd,
                            exit_code=rc_flush,
                            environment=task_env,
                            suggestion="Check the command output above for details",
                        )
                    pending_script = []

                i = 0
                while i < len(lines):
                    line = lines[i]
                    stripped = line.strip()

                    if not stripped or stripped.startswith('#'):
                        i += 1
                        continue

                    if stripped.startswith('env '):
                        flush_pending()
                        for tok in shlex.split(stripped)[1:]:
                            if '=' in tok:
                                k, v = tok.split('=', 1)
                                task_env[k] = _interpolate(v, params, task_env)
                        i += 1
                        continue

                    if stripped.startswith('shell_lang '):
                        flush_pending()
                        parts = stripped.split(None, 1)
                        shell_lang_value = parts[1].strip() if len(parts) > 1 else None
                        shell_lang_key = (shell_lang_value or "").lower()
                        if shell_lang_key in ("", "default"):
                            shell_lang = None
                            shell_lang_cleared = False
                        elif shell_lang_key == "none":
                            shell_lang = None
                            shell_lang_cleared = True
                        else:
                            shell_lang = shell_lang_value
                            shell_lang_cleared = False
                        i += 1
                        continue

                    if stripped.startswith('default_lang '):
                        flush_pending()
                        parts = stripped.split(None, 1)
                        implicit_lang = parts[1].strip() if len(parts) > 1 else None
                        i += 1
                        continue

                    try:
                        if stripped.startswith('shell '):
                            flush_pending()
                            shell_cmd = _interpolate(stripped[6:].strip(), params, task_env)

                            line_lang = None
                            # Allow per-line language with [lang:python] prefix
                            try:
                                line_lang, shell_cmd = _parse_lang_bracket(shell_cmd)
                                if line_lang:
                                    line_lang = _canonical_lang(line_lang)
                            except PFExecutionError as e:
                                raise PFExecutionError(
                                    message=e.message,
                                    task_name=task_name,
                                    command=stripped,
                                    suggestion=e.suggestion,
                                )

                            if shell_cmd.startswith("|"):
                                block_lines: List[str] = []
                                i += 1
                                while i < len(lines):
                                    next_line = lines[i]
                                    next_stripped = next_line.strip()
                                    if next_stripped.startswith(
                                        ('env ', 'shell ', 'shell_lang ', 'default_lang ', 'describe ', 'task ', 'end')
                                    ):
                                        break
                                    block_lines.append(next_line)
                                    i += 1
                                script_body = textwrap.dedent("\n".join(block_lines)).strip("\n")
                                lang_for_block = active_lang(line_lang)
                                if lang_for_block:
                                    rendered_cmd, _lang = _render_polyglot_command(
                                        lang_for_block, script_body, os.getcwd()
                                    )
                                    rc = _exec_line_fabric(
                                        rendered_cmd, connection, task_env, task_name,
                                        args.sudo, args.sudo_user
                                    )
                                else:
                                    heredoc_cmd = f"bash <<'PF_EOF'\n{script_body}\nPF_EOF"
                                    rc = _exec_line_fabric(
                                        heredoc_cmd, connection, task_env, task_name,
                                        args.sudo, args.sudo_user
                                    )
                            elif "<<" in shell_cmd:
                                # Parse heredoc syntax from the first line only (supports
                                # pre-grouped heredoc where body is embedded after '\n').
                                first_cmd_line = shell_cmd.split("\n")[0]
                                delimiter, outfile, strip_tabs = _parse_heredoc_syntax(first_cmd_line)
                                if delimiter:
                                    heredoc_lines: List[str] = []

                                    if "\n" in shell_cmd:
                                        # Pre-grouped heredoc: body is already embedded in
                                        # shell_cmd (as produced by parse_pfyfile_text).
                                        cmd_parts = shell_cmd.split("\n")
                                        shell_cmd = cmd_parts[0]
                                        found_delimiter = False
                                        for part in cmd_parts[1:]:
                                            if part.strip() == delimiter:
                                                found_delimiter = True
                                                break
                                            heredoc_lines.append(part)
                                        if not found_delimiter:
                                            raise PFExecutionError(
                                                message=f"Heredoc delimiter '{delimiter}' not found",
                                                task_name=task_name,
                                                command=shell_cmd,
                                                environment=task_env,
                                                suggestion="Ensure heredoc terminator is present",
                                            )
                                    else:
                                        i += 1
                                        while i < len(lines):
                                            body_line = lines[i]
                                            if body_line.strip() == delimiter:
                                                break
                                            heredoc_lines.append(body_line)
                                            i += 1
                                        else:
                                            raise PFExecutionError(
                                                message=f"Heredoc delimiter '{delimiter}' not found",
                                                task_name=task_name,
                                                command=shell_cmd,
                                                environment=task_env,
                                                suggestion="Ensure heredoc terminator is present"
                                            )

                                    heredoc_content = "\n".join(heredoc_lines)
                                    if strip_tabs:
                                        heredoc_content = "\n".join(line.lstrip("\t") for line in heredoc_lines)
                                    lang_for_heredoc = active_lang(line_lang)
                                    effective_lang = _canonical_lang(lang_for_heredoc) if lang_for_heredoc else None
                                    if lang_for_heredoc and effective_lang != "bash":
                                        rendered_cmd, _lang = _render_polyglot_command(
                                            lang_for_heredoc,
                                            textwrap.dedent(heredoc_content).strip("\n"),
                                            os.getcwd()
                                        )
                                        if outfile:
                                            rendered_cmd = f"(\n{rendered_cmd}\n) > {shlex.quote(outfile)}"
                                        rc = _exec_line_fabric(
                                            rendered_cmd, connection, task_env, task_name,
                                            args.sudo, args.sudo_user
                                        )
                                    else:
                                        # Native bash heredoc (or no lang).
                                        # If no command precedes '<<', run content via bash.
                                        cmd_before = shell_cmd.split("<<")[0].strip()
                                        if cmd_before:
                                            heredoc_cmd = f"{shell_cmd}\n{heredoc_content}\n{delimiter}"
                                        else:
                                            heredoc_cmd = f"bash {shell_cmd}\n{heredoc_content}\n{delimiter}"
                                        if outfile:
                                            heredoc_cmd = f"({heredoc_cmd}) > {shlex.quote(outfile)}"
                                        rc = _exec_line_fabric(
                                            heredoc_cmd, connection, task_env, task_name,
                                            args.sudo, args.sudo_user
                                        )
                                else:
                                    rc = execute_shell_command(
                                        shell_cmd, task_env, args.sudo, args.sudo_user,
                                        connection, prefix
                                    )
                            else:
                                rendered_cmd = None
                                lang_for_line = active_lang(line_lang)
                                if lang_for_line:
                                    rendered_cmd, _lang = _render_polyglot_command(
                                        lang_for_line, shell_cmd, os.getcwd()
                                    )
                                if rendered_cmd:
                                    rc = _exec_line_fabric(
                                        rendered_cmd, connection, task_env, task_name,
                                        args.sudo, args.sudo_user
                                    )
                                else:
                                    rc = execute_shell_command(
                                        shell_cmd, task_env, args.sudo, args.sudo_user,
                                        connection, prefix
                                    )

                            if rc != 0:
                                raise PFExecutionError(
                                    message=f"Command failed with exit code {rc}",
                                    task_name=task_name,
                                    command=shell_cmd,
                                    exit_code=rc,
                                    environment=task_env,
                                    suggestion="Check the command output above for details"
                                )

                            if not shell_cmd.startswith("|"):
                                i += 1
                            continue

                        if implicit_lang:
                            pending_script.append(line)
                        else:
                            print(f"{prefix}[skip] unsupported verb in task '{task_name}': {stripped}", file=sys.stderr)
                        i += 1
                        continue

                    except PFExecutionError:
                        raise
                    except Exception as e:
                        raise PFExecutionError(
                            message=f"Unexpected error executing command: {e}",
                            task_name=task_name,
                            command=line,
                            environment=task_env
                        )

                flush_pending()
            
            # Clean up connection
            if connection is not None:
                connection.close()
                
            return rc
        
        # Execute in parallel across hosts
        rc_total = 0
        executor = ThreadPoolExecutor(max_workers=min(32, len(hosts)))
        futures = {executor.submit(run_host, host): host for host in hosts}

        try:
            for future in as_completed(futures):
                try:
                    rc = future.result()
                except PFException as e:
                    print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
                    rc = 1
                except Exception as e:
                    print(format_exception_for_user(e, include_traceback=True), file=sys.stderr)
                    rc = 1
                rc_total = rc_total or rc
        except KeyboardInterrupt:
            for f in futures:
                f.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            print("Interrupted.", file=sys.stderr)
            return 130
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

        return rc_total


def main(argv: List[str]) -> int:
    """Main entry point for enhanced pf."""
    runner = PfRunner()
    return runner.run_command(argv)


def console_main() -> int:
    """Console script shim that forwards CLI args."""
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
