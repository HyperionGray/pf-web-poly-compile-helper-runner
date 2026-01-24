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
import difflib
import shlex
import textwrap
import re
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Import existing pf functionality
from pf_parser import (
    get_alias_map,
    _load_pfy_source_with_includes,
    _find_pfyfile,
    parse_pfyfile_text,
    Task,
    list_dsl_tasks_with_desc,
    _merge_env_hosts,
    _normalize_hosts,
    _parse_host,
    _c_for,
    _dedupe_preserve_order,
    _interpolate,
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


_PF_SHIM_MARKER = "pf-shim: generated"
_PF_SHIM_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_PF_TASK_HEADER_BLOCK_RE = re.compile(r"\[([^\]]+)\]")


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
                builtins = {
                    "list",
                    "help",
                    "run",
                    "prune",
                    "debug-on",
                    "debug-off",
                    "version",
                    "shim",
                }
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
            elif parsed_args.command == 'version':
                return self._handle_version_command(parsed_args)
            elif parsed_args.command == 'shim':
                return self._handle_shim_command(parsed_args)
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

    def _handle_shim_command(self, args) -> int:
        """Install/remove shell shims (PATH wrappers) that forward to pf."""
        action = getattr(args, "shim_action", None)
        if not action:
            raise PFException(
                message="Missing shim ACTION",
                suggestion="Usage: pf shim install|uninstall ... (run: pf shim --help)",
            )

        if action == "install":
            return self._handle_shim_install(args)
        if action == "uninstall":
            return self._handle_shim_uninstall(args)

        raise PFException(
            message=f"Unknown shim action: {action}",
            suggestion="Usage: pf shim install|uninstall ... (run: pf shim --help)",
        )

    def _handle_shim_install(self, args) -> int:
        names = [n for n in (getattr(args, "names", None) or []) if n]
        want_from_file = bool(getattr(args, "from_file", False))

        # Resolve Pfyfile path to bake into wrappers.
        pfyfile = _find_pfyfile(file_arg=getattr(args, "file", None))
        pfyfile_abs = os.path.abspath(pfyfile)
        if not os.path.isfile(pfyfile_abs):
            raise PFException(
                message=f"Pfyfile not found: {pfyfile_abs}",
                suggestion="Run from a project directory with Pfyfile.pf or pass --file/-f",
            )

        declared: List[str] = []
        if want_from_file:
            try:
                dsl_src, _task_sources = _load_pfy_source_with_includes(
                    file_arg=getattr(args, "file", None)
                )
            except Exception as e:
                raise PFException(
                    message=f"Failed to load Pfyfile for [shim ...] discovery: {e}",
                    suggestion="Check your Pfyfile includes or pass --file/-f",
                )
            declared = sorted(self._extract_shims_from_task_headers(dsl_src))

        install_names = []
        for name in [*names, *declared]:
            if name not in install_names:
                install_names.append(name)

        if not install_names:
            raise PFException(
                message="No shim names provided",
                suggestion="Usage: pf shim install nk nkctl  OR  pf shim install --from-file",
            )

        bin_dir = getattr(args, "bin_dir", None) or os.path.expanduser("~/.local/bin")
        bin_dir = os.path.abspath(os.path.expanduser(bin_dir))
        Path(bin_dir).mkdir(parents=True, exist_ok=True)

        force = bool(getattr(args, "force", False))

        failed: List[str] = []
        installed: List[str] = []

        for name in install_names:
            if not self._is_valid_shim_name(name):
                failed.append(name)
                print(
                    f"Error: invalid shim name: {name!r} (allowed: letters/numbers/._-; no spaces or slashes)",
                    file=sys.stderr,
                )
                continue

            target = os.path.join(bin_dir, name)
            if os.path.isdir(target):
                failed.append(name)
                print(f"Error: shim path is a directory: {target}", file=sys.stderr)
                continue

            if os.path.exists(target):
                try:
                    existing = Path(target).read_text(encoding="utf-8", errors="replace")
                except Exception:
                    existing = ""
                managed = _PF_SHIM_MARKER in existing
                if not managed and not force:
                    failed.append(name)
                    print(
                        f"Error: {target} already exists (use --force to overwrite)",
                        file=sys.stderr,
                    )
                    continue

            script = self._render_shim_script(pfyfile_abs)
            try:
                Path(target).write_text(script, encoding="utf-8")
                os.chmod(target, 0o755)
                installed.append(name)
            except Exception as e:
                failed.append(name)
                print(f"Error: failed to write shim {target}: {e}", file=sys.stderr)

        if installed:
            print(f"Installed shims to {bin_dir}: {', '.join(installed)}")

        if failed:
            print(
                f"Failed to install shims: {', '.join(failed)}",
                file=sys.stderr,
            )
            return 1

        return 0

    def _handle_shim_uninstall(self, args) -> int:
        names = [n for n in (getattr(args, "names", None) or []) if n]
        if not names:
            raise PFException(
                message="No shim names provided",
                suggestion="Usage: pf shim uninstall nk nkctl",
            )

        bin_dir = getattr(args, "bin_dir", None) or os.path.expanduser("~/.local/bin")
        bin_dir = os.path.abspath(os.path.expanduser(bin_dir))
        force = bool(getattr(args, "force", False))

        failed: List[str] = []
        removed: List[str] = []

        for name in names:
            if not self._is_valid_shim_name(name):
                failed.append(name)
                print(f"Error: invalid shim name: {name!r}", file=sys.stderr)
                continue

            target = os.path.join(bin_dir, name)
            if not os.path.exists(target):
                print(f"Note: shim not found: {target}", file=sys.stderr)
                continue

            if os.path.isdir(target):
                failed.append(name)
                print(f"Error: shim path is a directory: {target}", file=sys.stderr)
                continue

            managed = False
            try:
                existing = Path(target).read_text(encoding="utf-8", errors="replace")
                managed = _PF_SHIM_MARKER in existing
            except Exception:
                managed = False

            if not managed and not force:
                failed.append(name)
                print(
                    f"Error: refusing to remove unmanaged file: {target} (use --force)",
                    file=sys.stderr,
                )
                continue

            try:
                os.remove(target)
                removed.append(name)
            except Exception as e:
                failed.append(name)
                print(f"Error: failed to remove {target}: {e}", file=sys.stderr)

        if removed:
            print(f"Removed shims from {bin_dir}: {', '.join(removed)}")

        if failed:
            print(f"Failed to remove shims: {', '.join(failed)}", file=sys.stderr)
            return 1

        return 0

    def _extract_shims_from_task_headers(self, dsl_src: str) -> List[str]:
        """Extract shim names declared in task headers via [shim ...]."""
        shims: List[str] = []
        for raw in dsl_src.splitlines():
            stripped = raw.strip()
            if not stripped.startswith("task "):
                continue

            rest = stripped[5:].strip()
            for match in _PF_TASK_HEADER_BLOCK_RE.finditer(rest):
                block = match.group(1)
                for part in block.split("|"):
                    part = part.strip()
                    if not part:
                        continue

                    value = None
                    if part.startswith("shim="):
                        value = part[len("shim="):].strip()
                    elif part.startswith("shim "):
                        value = part[len("shim "):].strip()

                    if not value:
                        continue

                    value = value.strip().strip("'\"")
                    for name in [n.strip() for n in value.split(",")]:
                        if not name:
                            continue
                        if name not in shims:
                            shims.append(name)

        return shims

    def _is_valid_shim_name(self, name: str) -> bool:
        if not name or "/" in name or "\x00" in name or " " in name:
            return False
        return bool(_PF_SHIM_NAME_RE.match(name))

    def _render_shim_script(self, pfyfile_abs: str) -> str:
        # bash is intentionally hard-coded: this shim is a tiny, portable wrapper.
        pfyfile_quoted = shlex.quote(pfyfile_abs)
        return (
            "#!/usr/bin/env bash\n"
            f"# {_PF_SHIM_MARKER}\n"
            f"# pfyfile: {pfyfile_abs}\n"
            "set -euo pipefail\n"
            f'PFYFILE={pfyfile_quoted}\n'
            'cd "$(dirname "$PFYFILE")"\n'
            'cmd="$(basename "$0")"\n'
            'exec pf --file "$PFYFILE" "$cmd" "$@"\n'
        )
    
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

            # Allow "spaced" task invocation by joining adjacent words with '-' / '_'
            # (e.g. `pf nk up` -> `nk-up`, `pf nkctl join` -> `nkctl-join`).
            if (
                os.getenv("PF_TASK_WORDS", "on").lower() not in ("0", "false", "off", "no")
                and (
                    task_name not in valid_task_names
                    or (
                        task_name in valid_task_names
                        and i + 1 < len(task_args)
                        and "=" not in task_args[i + 1]
                        and not task_args[i + 1].startswith("-")
                        and task_args[i + 1] not in valid_task_names
                    )
                )
            ):
                max_words_raw = os.getenv("PF_TASK_WORDS_MAX", "6")
                try:
                    max_words = max(2, int(max_words_raw))
                except Exception:
                    max_words = 6

                best_name: Optional[str] = None
                best_words = 0
                for words in range(2, max_words + 1):
                    end = i + words
                    if end > len(task_args):
                        break
                    seg = task_args[i:end]
                    # Stop at parameter/flag boundaries.
                    if any("=" in s for s in seg):
                        break
                    if any(s.startswith("-") for s in seg[1:]):
                        break

                    cand_dash = "-".join(seg)
                    if cand_dash in valid_task_names:
                        best_name = cand_dash
                        best_words = words
                        continue
                    cand_us = "_".join(seg)
                    if cand_us in valid_task_names:
                        best_name = cand_us
                        best_words = words

                if best_name:
                    if os.getenv("PF_DEBUG_TASK_WORDS", "0").lower() in ("1", "true", "yes", "on"):
                        print(
                            f"Info: interpreting task words '{' '.join(task_args[i:i+best_words])}' as '{best_name}'",
                            file=sys.stderr,
                        )
                    resolved_name = best_name
                    i += best_words
                else:
                    # Resolve/auto-correct task name when it is not an exact match
                    resolved_name = self._resolve_task_name(task_name, valid_task_names)
                    i += 1
            else:
                # Resolve/auto-correct task name when it is not an exact match
                resolved_name = self._resolve_task_name(task_name, valid_task_names)
                i += 1
            
            # Parse parameters for this task
            params: Dict[str, str] = {}
            # Start with task-defined defaults (if any), then override with CLI args.
            if resolved_name in dsl_tasks:
                params.update(dsl_tasks[resolved_name].params or {})

            # Parse key=value and --key=value forms.
            while i < len(task_args) and '=' in task_args[i]:
                raw = task_args[i]
                key, value = raw.split('=', 1)
                if key.startswith('--'):
                    key = key[2:]
                if not key:
                    break
                params[key] = value
                i += 1
            
            # Get task lines
            if resolved_name in BUILTINS:
                lines = BUILTINS[resolved_name]
            else:
                lines = dsl_tasks[resolved_name].lines
            
            selected.append((resolved_name, lines, params))
        
        return selected

    def _resolve_task_name(self, task_name: str, valid_task_names: set) -> str:
        """Return a valid task name, applying autocorrect with user-controlled policy."""
        if task_name in valid_task_names:
            return task_name

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
                connection, _resolved = _c_for(spec, args.sudo, args.sudo_user)
                
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
                # Expose task params as environment variables for convenience (and for polyglot blocks).
                task_env = dict(params)
                current_lang = None
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    stripped = line.strip()

                    if not stripped or stripped.startswith("#"):
                        i += 1
                        continue

                    # Handle env command (stateful)
                    if stripped.startswith("env "):
                        for tok in shlex.split(stripped)[1:]:
                            if "=" in tok:
                                k, v = tok.split("=", 1)
                                task_env[k] = _interpolate(v, params, task_env)
                        i += 1
                        continue

                    # Track shell_lang hint for subsequent shell commands
                    if stripped.startswith("shell_lang "):
                        parts = stripped.split(None, 1)
                        current_lang = parts[1].strip() if len(parts) > 1 else None
                        i += 1
                        continue

                    try:
                        # Use enhanced shell execution for shell commands
                        if stripped.startswith("shell "):
                            shell_cmd = stripped[6:].strip()  # Remove 'shell ' prefix
                            shell_cmd = _interpolate(shell_cmd, params, task_env)

                            # Handle multiline pipe-style blocks: "shell |\n  ...".
                            if shell_cmd.startswith("|"):
                                # The parser may either:
                                #   1) embed the whole block into this single line (preferred), e.g.
                                #        shell |\n  echo hi\n  ...
                                #   2) keep "shell |" as-is and store block lines as subsequent task lines (legacy)
                                if "\n" in shell_cmd:
                                    block_lines = shell_cmd.splitlines()[1:]
                                    script_body = textwrap.dedent("\n".join(block_lines))
                                    i += 1
                                else:
                                    block_lines = []
                                    i += 1
                                    while i < len(lines):
                                        next_line = lines[i]
                                        next_stripped = next_line.strip()
                                        if next_stripped.startswith(
                                            (
                                                "env ",
                                                "shell ",
                                                "shell_lang ",
                                                "default_lang ",
                                                "describe ",
                                                "task ",
                                                "end",
                                            )
                                        ):
                                            break
                                        block_lines.append(next_line.lstrip())
                                        i += 1
                                    script_body = textwrap.dedent("\n".join(block_lines))

                                # If shell_lang is set, run the block via the polyglot builder.
                                # Otherwise default to bash via heredoc.
                                failed_cmd = ""
                                if current_lang:
                                    rendered_cmd, _lang = _render_polyglot_command(
                                        current_lang, script_body, os.getcwd()
                                    )
                                    failed_cmd = rendered_cmd or ""
                                    rc = _exec_line_fabric(
                                        rendered_cmd, connection, task_env, task_name,
                                        args.sudo, args.sudo_user
                                    )
                                else:
                                    heredoc_cmd = f"bash <<'PF_EOF'\n{script_body}\nPF_EOF"
                                    failed_cmd = heredoc_cmd
                                    rc = _exec_line_fabric(
                                        heredoc_cmd, connection, task_env, task_name,
                                        args.sudo, args.sudo_user
                                    )
                                if rc != 0:
                                    raise PFExecutionError(
                                        message=f"Command failed with exit code {rc}",
                                        task_name=task_name,
                                        command=failed_cmd,
                                        exit_code=rc,
                                        environment=task_env,
                                        suggestion="Check the command output above for details"
                                    )
                                continue

                            # If a default language is set, render polyglot wrapper
                            rendered_cmd = None
                            if current_lang:
                                rendered_cmd, _lang = _render_polyglot_command(
                                    current_lang, shell_cmd, os.getcwd()
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
                        else:
                            # If shell_lang is active, treat bare lines as a language block.
                            # This lets users write e.g.:
                            #   shell_lang python
                            #   import os
                            #   print(os.getcwd())
                            # without needing to prefix every line with `shell`.
                            if current_lang:
                                block_lines = [line]
                                j = i + 1
                                while j < len(lines):
                                    nxt = lines[j]
                                    nxt_stripped = nxt.strip()

                                    if not nxt_stripped or nxt_stripped.startswith("#"):
                                        block_lines.append(nxt)
                                        j += 1
                                        continue

                                    if nxt_stripped.startswith(
                                        ("env ", "shell ", "shell_lang ", "default_lang ")
                                    ):
                                        break

                                    block_lines.append(nxt)
                                    j += 1

                                script_body = textwrap.dedent("\n".join(block_lines))
                                script_body = _interpolate(script_body, params, task_env)
                                rendered_cmd, _lang = _render_polyglot_command(
                                    current_lang, script_body, os.getcwd()
                                )
                                cmd_for_error = rendered_cmd or script_body
                                rc = _exec_line_fabric(
                                    rendered_cmd or script_body,
                                    connection,
                                    task_env,
                                    task_name,
                                    args.sudo,
                                    args.sudo_user,
                                )
                                if rc != 0:
                                    raise PFExecutionError(
                                        message=f"Command failed with exit code {rc}",
                                        task_name=task_name,
                                        command=cmd_for_error,
                                        exit_code=rc,
                                        environment=task_env,
                                        suggestion="Check the command output above for details",
                                    )
                                i = j
                                continue

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

                    i += 1
            
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


def console_main() -> int:
    """Console script shim that forwards CLI args."""
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
