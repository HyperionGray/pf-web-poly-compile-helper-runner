#!/usr/bin/env python3
"""
pf_runner_core.py - Core pf runner implementation with subcommand support

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
import shlex
import traceback
import difflib
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Central JSON5 config (no PF_* env vars for configuration)
import pf_config

# Import existing pf functionality
import pf_parser as pf_parser_module
from pf_parser import (
    get_alias_map,
    _find_pfyfile,
    _load_pfy_source_with_includes,
    parse_pfyfile_text,
    Task,
    _merge_env_hosts,
    _normalize_hosts,
    _parse_host,
    _c_for,
    _dedupe_preserve_order,
    _interpolate,
    _exec_line_fabric,
    BUILTINS,
)
from pf_args import PfArgumentParser, HELP_VARIATIONS
from pf_exceptions import (
    PFException,
    PFConnectionError,
    PFExecutionError,
    PFTaskNotFoundError,
    format_exception_for_user,
)

# Import specialized components
from pf_subcommand_manager import SubcommandManager
from pf_builtin_commands import BuiltinCommandHandler
from pf_task_executor import TaskExecutor
from pf_shell import execute_shell_command
from pf_polyglot import render_polyglot_command
from pfuck import PfAutocorrect


_LANG_BRACKET_RE = re.compile(r"^\s*\[lang:([^\]]+)\]\s*(.*)$", re.IGNORECASE | re.DOTALL)
_POLYGLOT_HEREDOC_HEADER_RE = re.compile(
    r"^\s*<<-?\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:>\s*([^\s]+))?\s*$"
)


def _extract_polyglot_heredoc(cmd: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Extract a polyglot heredoc body.

    Supported forms (after stripping any leading `shell` and `[lang:...]` prefixes):
      << DELIM
      <code>
      DELIM

      << DELIM > /path/to/output.txt
      <code>
      DELIM

    Returns:
      (code, output_path) or None when cmd is not a polyglot heredoc.
    """
    if "\n" not in cmd:
        return None

    lines = cmd.splitlines()
    if not lines:
        return None

    header = lines[0].strip()
    m = _POLYGLOT_HEREDOC_HEADER_RE.match(header)
    if not m:
        return None

    delimiter = m.group(1)
    output_path = m.group(2)

    terminator_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == delimiter:
            terminator_idx = idx
            break

    if terminator_idx is None:
        raise PFExecutionError(
            message=f"Unclosed heredoc: missing terminator '{delimiter}'",
            command=header,
            suggestion=f"Add a line containing only {delimiter} to close the heredoc",
        )

    code = "\n".join(lines[1:terminator_idx])
    if code and not code.endswith("\n"):
        code += "\n"
    return code, output_path


class PfRunner:
    """Enhanced pf runner with subcommand support and modular architecture."""
    
    # Shell metacharacters that require quoting when present in command tokens
    SHELL_METACHARACTERS = {';', '|', '&', '$', '`', '"', "'", ' '}
    
    def __init__(self):
        self.arg_parser = PfArgumentParser()
        self.subcommand_manager = SubcommandManager()
        self.builtin_handler = BuiltinCommandHandler()
        self.task_executor = TaskExecutor()
        self.autocorrect = None
        self.config = None
        self.config_path = None

    @staticmethod
    def _needs_shell_quoting(token: str) -> bool:
        """
        Check if a token needs shell quoting.
        
        Returns True if the token contains any shell metacharacters that would
        require quoting to prevent shell interpretation.
        """
        return any(c in token for c in PfRunner.SHELL_METACHARACTERS)

    def _maybe_update_bashrc_aliases(self, dsl_tasks: Dict[str, Task]) -> None:
        """Best-effort: export `rc=true` tasks as bash aliases in ~/.bashrc."""
        # Avoid modifying user rc files in non-interactive contexts (CI, `pf list | head`, etc).
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return

        if os.environ.get("PF_NO_RC", "").strip().lower() in {"1", "true", "yes", "on"}:
            return

        exportable: List[Task] = [t for t in dsl_tasks.values() if getattr(t, "rc", False)]
        if not exportable:
            return

        bashrc = os.path.expanduser("~/.bashrc")
        if not bashrc or bashrc == "~/.bashrc":
            return

        begin = "# >>> pf rc=true aliases >>>"
        end = "# <<< pf rc=true aliases <<<"

        alias_lines: List[str] = []
        for task in sorted(exportable, key=lambda t: t.name):
            name = task.name.strip()
            if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]*$", name):
                continue
            alias_lines.append(f"alias {name}={shlex.quote(f'pf {name}')}")

        block = "\n".join(
            [
                begin,
                "# Generated by pf-runner. Set PF_NO_RC=1 to disable.",
                *alias_lines,
                end,
                "",
            ]
        )

        try:
            existing = ""
            if os.path.exists(bashrc):
                with open(bashrc, "r", encoding="utf-8") as f:
                    existing = f.read()

            if begin in existing and end in existing and existing.index(begin) < existing.index(end):
                before = existing[: existing.index(begin)].rstrip("\n")
                after = existing[existing.index(end) + len(end) :].lstrip("\n")
                updated = before + "\n\n" + block + after
            else:
                base = existing.rstrip("\n")
                updated = (base + "\n\n" + block) if base else block

            if updated != existing:
                with open(bashrc, "w", encoding="utf-8") as f:
                    f.write(updated)
        except Exception as e:
            print(f"[warn] failed to update {bashrc}: {e}", file=sys.stderr)

    def _extract_config_arg(self, args: List[str]) -> Optional[str]:
        i = 0
        while i < len(args):
            if args[i] == "--config" and i + 1 < len(args):
                return args[i + 1]
            if args[i].startswith("--config="):
                return args[i].split("=", 1)[1]
            i += 1
        return None

    def _extract_positional_args(self, args: List[str]) -> Tuple[List[str], Optional[str]]:
        """Extract non-option args plus any explicit -f/--file value."""
        positional: List[str] = []
        file_arg: Optional[str] = None

        i = 0
        while i < len(args):
            arg = args[i]

            if arg in ("-f", "--file", "--config", "--env", "--hosts", "--host", "--user", "--port", "--sudo-user"):
                if i + 1 < len(args):
                    if arg in ("-f", "--file"):
                        file_arg = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue

            if arg.startswith("--file="):
                file_arg = arg.split("=", 1)[1]
                i += 1
                continue

            if arg.startswith(("--config=", "--env=", "--hosts=", "--host=", "--user=", "--port=", "--sudo-user=")):
                i += 1
                continue

            if arg == "--sudo":
                i += 1
                continue

            if arg.startswith("-") and arg not in HELP_VARIATIONS:
                i += 1
                continue

            positional.append(arg)
            i += 1

        return positional, file_arg

    def _load_and_apply_config(self, explicit_path: Optional[str]) -> None:
        cfg, resolved = pf_config.load_config(
            start_dir=os.getcwd(),
            explicit_path=explicit_path,
            require_exists=bool(explicit_path),
        )
        self.config = cfg
        self.config_path = str(resolved) if resolved else None
        pf_parser_module.configure(cfg, self.config_path)
        
    def discover_subcommands(self, pfyfile: Optional[str] = None) -> Dict[str, List[str]]:
        """Discover subcommands from included files."""
        subcommands: Dict[str, List[str]] = {}
        
        try:
            # Load the main pfy source with includes
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfyfile)

            # Group tasks by source file (include file) using task_sources
            main_file = None
            try:
                main_candidate = _find_pfyfile(file_arg=pfyfile)
                if os.path.exists(main_candidate):
                    main_file = os.path.abspath(main_candidate)
            except Exception:
                main_file = None

            tasks_by_source: Dict[str, List[str]] = {}
            for task_name, src in task_sources.items():
                if not src:
                    continue
                src_path = os.path.abspath(src)
                if main_file and src_path == main_file:
                    continue
                tasks_by_source.setdefault(src_path, []).append(task_name)

            for src_path, task_names in tasks_by_source.items():
                basename = os.path.basename(src_path)
                if not (basename.startswith("Pfyfile.") and basename.endswith(".pf")):
                    continue
                if basename == "Pfyfile.always-available.pf":
                    continue
                try:
                    # Add subcommand to parser
                    self.arg_parser.add_subcommand_from_file(src_path, task_names)
                    # Store for reference
                    subcommands[src_path] = task_names
                except Exception as e:
                    # Warn about other errors but don't fail
                    print(f"Warning: Could not register subcommands from {basename}: {e}", file=sys.stderr)
                    
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

        # Load config early so subcommand discovery + Pfyfile lookup behave consistently.
        self._load_and_apply_config(self._extract_config_arg(args))
        
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

        # Discover subcommands (requires loading Pfyfile/includes)
        self.discover_subcommands(pfyfile=file_arg)
        
        # Parse arguments
        try:
            # Allow "pf <task> --help" and "pf run <task> --help" for task help
            if any(arg in HELP_VARIATIONS for arg in args):
                positional, help_file_arg = self._extract_positional_args(args)
                if positional:
                    primary = positional[0]
                    builtins = {"list", "help", "run", "prune", "debug-on", "debug-off", "version"}
                    subcommands = getattr(self.arg_parser, "_subcommand_names", set())

                    def _task_tokens_after(idx: int) -> List[str]:
                        tokens: List[str] = []
                        for tok in positional[idx:]:
                            if tok in HELP_VARIATIONS or "=" in tok:
                                break
                            tokens.append(tok)
                        return tokens

                    if primary == "run":
                        task_tokens = _task_tokens_after(1)
                        if task_tokens:
                            return self._show_task_help("-".join(task_tokens), help_file_arg)
                    elif primary in subcommands:
                        task_tokens = _task_tokens_after(1)
                        if task_tokens:
                            return self._show_task_help("-".join(task_tokens), help_file_arg)
                    elif primary not in builtins and primary not in subcommands and primary not in HELP_VARIATIONS:
                        task_tokens = _task_tokens_after(0)
                        if task_tokens:
                            return self._show_task_help("-".join(task_tokens), help_file_arg)

            # Parse arguments
            try:
                parsed_args = self.arg_parser.parse_args(args)
            except SystemExit as e:
                return e.code if e.code is not None else 1

            # Re-load config using parsed args (allows --config anywhere).
            self._load_and_apply_config(getattr(parsed_args, "config", None))
                
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
        try:
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=args.file)
            dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)
            self._maybe_update_bashrc_aliases(dsl_tasks)

            if args.subcommand:
                print(f"Tasks for {args.subcommand}:")
            else:
                print("Available tasks:")

            if not dsl_tasks:
                print("  No tasks found.")
                if args.file:
                    print(f"\nNote: Using Pfyfile: {args.file}")
                    print("Check if the file exists and contains task definitions.")
                else:
                    print("\nNote: No Pfyfile.pf found in current directory or parent directories.")
                    print("Create a Pfyfile.pf or specify one with: pf -f <path> list")
                return 0

            def _group_name_for_source_file(source_file: Optional[str]) -> str:
                if not source_file:
                    return "embedded"
                base = os.path.basename(source_file)
                name = base[:-3] if base.endswith(".pf") else os.path.splitext(base)[0]
                if name.startswith("Pfyfile."):
                    name = name[len("Pfyfile.") :]
                return name or base

            grouped: Dict[Optional[str], List[Task]] = {}
            for task in dsl_tasks.values():
                grouped.setdefault(task.source_file, []).append(task)

            # Optional filtering: treat --subcommand as a file-group selector
            if args.subcommand:
                wanted = args.subcommand.strip().lower()
                grouped = {
                    src: tasks
                    for src, tasks in grouped.items()
                    if _group_name_for_source_file(src).strip().lower() == wanted
                }

            main_file = os.path.abspath(_find_pfyfile(file_arg=args.file))

            def _group_sort_key(item: Tuple[Optional[str], List[Task]]):
                src, _ = item
                if src and os.path.abspath(src) == main_file:
                    return (0, "")
                return (1, _group_name_for_source_file(src).lower())

            for src, tasks in sorted(grouped.items(), key=_group_sort_key):
                group_name = _group_name_for_source_file(src)
                src_label = os.path.basename(src) if src else "embedded"
                print(f"\n{group_name} ({src_label}):")
                for task in sorted(tasks, key=lambda t: t.name):
                    desc_text = f" - {task.description}" if task.description else ""
                    alias_text = (
                        f" (aliases: {', '.join(task.aliases)})" if task.aliases else ""
                    )
                    print(f"  {task.name}{desc_text}{alias_text}")
                    
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
            # If the user asked for a subcommand's help, defer to argparse.
            if task_name in getattr(self.arg_parser, "_subcommand_names", set()):
                try:
                    self.arg_parser.parser.parse_args([task_name, "--help"])
                except SystemExit as e:
                    return e.code if e.code is not None else 0
                return 0

            if self.autocorrect is None:
                self.autocorrect = PfAutocorrect(pfyfile)

            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=pfyfile)
            dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)

            def _print_section(title: str, lines: List[str]) -> None:
                if not lines:
                    return
                print(f"\n{title}:")
                for line in lines:
                    print(f"  {line}")

            task = dsl_tasks.get(task_name)
            if task is None:
                alias_map = {}
                for t in dsl_tasks.values():
                    for alias in t.aliases:
                        alias_map[alias] = t.name
                if task_name in alias_map:
                    task = dsl_tasks.get(alias_map[task_name])

            if task:
                print(f"Task: {task.name}")
                if task.description:
                    print(f"Description: {task.description}")
                if task.synopsis:
                    print(f"Synopsis: {task.synopsis}")
                if task.category:
                    print(f"Category: {task.category}")
                if task.aliases:
                    print(f"Aliases: {', '.join(task.aliases)}")
                if task.source_file:
                    try:
                        rel_source = os.path.relpath(task.source_file, os.getcwd())
                    except Exception:
                        rel_source = task.source_file
                    print(f"Source: {rel_source}")

                usage_parts = (
                    [f"{k}=<{k}>" for k in task.params.keys()] if task.params else []
                )
                usage_line = "pf " + task.name
                usage_run_line = "pf run " + task.name
                usage_subcommand_line = None
                if task.source_file:
                    base = os.path.basename(task.source_file)
                    if base.startswith("Pfyfile.") and base.endswith(".pf"):
                        subcommand = base[8:-3].replace("_", "-")
                        if subcommand and subcommand != "pf":
                            usage_subcommand_line = "pf " + subcommand + " " + task.name
                if usage_parts:
                    args_text = " ".join(usage_parts)
                    usage_line += " " + args_text
                    usage_run_line += " " + args_text
                    if usage_subcommand_line:
                        usage_subcommand_line += " " + args_text
                print("\nUsage:")
                if usage_subcommand_line:
                    print(f"  {usage_subcommand_line}")
                print(f"  {usage_line}")
                if usage_run_line != usage_line:
                    print(f"  {usage_run_line}")

                if task.params:
                    param_lines = []
                    for key, value in task.params.items():
                        default_value = value if value not in (None, "") else "<empty>"
                        description = ""
                        if getattr(task, "param_help", None):
                            description = task.param_help.get(key, "")
                        if description:
                            param_lines.append(
                                f"{key} (default: {default_value}) - {description}"
                            )
                        else:
                            param_lines.append(f"{key} (default: {default_value})")
                    _print_section("Parameters", param_lines)

                _print_section("Examples", task.examples)
                _print_section("Prerequisites", task.prerequisites)
                _print_section("Use Cases", task.use_cases)
                _print_section("Notes", task.notes)
                _print_section("Troubleshooting", task.troubleshooting)
                _print_section("See Also", task.see_also)
                if task.tags:
                    _print_section("Tags", [", ".join(task.tags)])

                _print_section("Commands", task.lines)
                return 0

            if task_name in BUILTINS:
                print(f"Built-in task: {task_name}")
                print(f"\nUsage:\n  pf {task_name}")
                _print_section("Commands", BUILTINS[task_name])
                return 0

            # Try to suggest corrections
            suggestions = self.autocorrect.suggest_task_correction(task_name)
            print(f"Task '{task_name}' not found.")
            if suggestions:
                print("Did you mean:")
                for suggestion in suggestions:
                    print(f"  {suggestion}")
            return 1

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
            self._maybe_update_bashrc_aliases(dsl_tasks)
            valid_task_names = set(BUILTINS.keys()) | set(dsl_tasks.keys())

            help_task = self._extract_task_help_request(task_args, valid_task_names)
            if help_task:
                return self._show_task_help(help_task, args.file)
            
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

    def _extract_task_help_request(
        self, task_args: List[str], valid_task_names: set
    ) -> Optional[str]:
        """Detect inline task help requests like `pf task --help`."""
        if not task_args:
            return None
        help_flags = {"--help", "-h"}
        raw_task_name, consumed = self._consume_task_name(task_args, 0, valid_task_names)
        if not raw_task_name:
            return None
        remaining = task_args[consumed:]
        if not remaining:
            return None
        if all(tok in help_flags for tok in remaining):
            return raw_task_name
        return None
    
    def _parse_task_arguments(
        self,
        task_args: List[str],
        valid_task_names: set,
        dsl_tasks: Dict[str, Task],
    ) -> List[Tuple[str, List[str], Dict[str, str], Optional[str]]]:
        """Parse task arguments into (task_name, lines, params, source_file) tuples."""
        selected = []
        i = 0
        
        while i < len(task_args):
            raw_task_name, consumed = self._consume_task_name(task_args, i, valid_task_names)

            # Resolve/auto-correct task name when it is not an exact match
            resolved_name = self._resolve_task_name(raw_task_name, valid_task_names)

            i += consumed
            
            # Parse parameters for this task
            params = {}
            while i < len(task_args) and '=' in task_args[i] and not task_args[i].startswith('--'):
                key, value = task_args[i].split('=', 1)
                params[key] = value
                i += 1
            
            # Get task lines
            source_file = None
            if resolved_name in BUILTINS:
                lines = BUILTINS[resolved_name]
            else:
                task_obj = dsl_tasks[resolved_name]
                lines = task_obj.lines
                source_file = task_obj.source_file

                # Start with default parameters from task definition
                merged_params = dict(task_obj.params)
                # Override with provided parameters
                merged_params.update(params)
                params = merged_params
            
            selected.append((resolved_name, lines, params, source_file))
        
        return selected

    def _consume_task_name(self, args: List[str], start: int, valid_task_names: set) -> Tuple[str, int]:
        """
        Consume a task name from args[start:], supporting "multi-word" invocations.

        Example:
          task name: do-this-thing
          invocation: pf do this thing
        """
        if start >= len(args):
            return "", 0

        first = args[start]
        if first in valid_task_names:
            return first, 1

        # Try joining consecutive tokens with '-' to match hyphenated task names.
        best_name = first
        best_len = 1

        end = start
        while end < len(args):
            token = args[end]
            if end > start and (token.startswith("--") or "=" in token):
                break

            candidate = "-".join(args[start : end + 1])
            if candidate in valid_task_names:
                best_name = candidate
                best_len = (end - start) + 1
            end += 1

        return best_name, best_len

    def _resolve_task_name(self, task_name: str, valid_task_names: set) -> str:
        """Return a valid task name, applying autocorrect with user-controlled policy."""
        if task_name in valid_task_names:
            return task_name

        mode = str(pf_config.get(self.config or {}, "runner.autocorrect.mode", "auto")).lower()
        threshold = pf_config.get_float(self.config or {}, "runner.autocorrect.threshold", 0.75)

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
                f"(confidence {score:.2f}). Set runner.autocorrect.mode='off' in pf.config.json5 to disable.",
                file=sys.stderr,
            )
            return best

        _fail()

    def _task_cwd_for(self, source_file: Optional[str]) -> Optional[str]:
        if source_file:
            return os.path.dirname(os.path.abspath(source_file)) or None
        pfy_root = getattr(pf_parser_module, "PFY_ROOT", None)
        if pfy_root:
            return os.path.abspath(pfy_root)
        return None

    def _path_autofix_enabled(self) -> bool:
        return pf_config.get_bool(self.config or {}, "runner.pathAutofix", True)

    def _looks_like_path(self, value: str) -> bool:
        if not value:
            return False
        if value.startswith("-"):
            return False
        if "://" in value or value.startswith("git@"):
            return False
        if "$" in value:
            # Avoid guessing when the value contains interpolation.
            return False
        if value in {".", ".."}:
            return True
        if value.startswith(("./", "../", "~")):
            return True
        if "/" in value or "\\" in value:
            return True

        lower = value.lower()
        return lower.endswith(
            (
                ".pf",
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
                ".md",
                ".txt",
                ".rs",
                ".c",
                ".cpp",
                ".h",
                ".hpp",
                ".go",
                ".java",
                ".kt",
                ".cs",
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".ps1",
                ".wasm",
            )
        )

    def _autofix_path_value(
        self,
        key: str,
        value: str,
        invocation_cwd: str,
        task_cwd: Optional[str],
    ) -> Tuple[str, Optional[str]]:
        if not self._looks_like_path(value):
            return value, None

        expanded = os.path.expanduser(os.path.expandvars(value))
        if "$" in expanded:
            return value, None

        if os.path.isabs(expanded):
            if expanded != value and os.path.exists(expanded):
                return expanded, f"param '{key}' expanded '{value}' -> '{expanded}'"
            return value, None

        inv_path = os.path.abspath(os.path.join(invocation_cwd, expanded))
        if os.path.exists(inv_path):
            return (
                inv_path,
                f"param '{key}' resolved '{value}' -> '{inv_path}' (relative to invocation cwd)",
            )

        if task_cwd:
            task_path = os.path.abspath(os.path.join(task_cwd, expanded))
            if os.path.exists(task_path):
                return (
                    task_path,
                    f"param '{key}' resolved '{value}' -> '{task_path}' (relative to task file)",
                )

        # Last resort: search for a matching basename in a few likely roots.
        basename = os.path.basename(expanded.rstrip("/\\"))
        if not basename:
            return value, None

        roots: List[str] = []
        for root in (task_cwd, getattr(pf_parser_module, "PFY_ROOT", None), invocation_cwd):
            if root and os.path.isdir(root):
                root_abs = os.path.abspath(root)
                if root_abs not in roots:
                    roots.append(root_abs)

        skip_dirs = {
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
            "target",
        }

        matches: List[str] = []
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in skip_dirs]
                if basename in dirnames:
                    matches.append(os.path.join(dirpath, basename))
                if basename in filenames:
                    matches.append(os.path.join(dirpath, basename))
                if len(matches) > 25:
                    break
            if len(matches) > 25:
                break

        if not matches:
            return value, None

        tail = os.path.normpath(expanded).replace("\\", "/")
        suffix_matches = [m for m in matches if m.replace("\\", "/").endswith(tail)]
        if len(suffix_matches) == 1:
            chosen = os.path.abspath(suffix_matches[0])
            return (
                chosen,
                f"param '{key}' resolved '{value}' -> '{chosen}' (searched project for suffix match)",
            )

        if len(matches) == 1:
            chosen = os.path.abspath(matches[0])
            return (
                chosen,
                f"param '{key}' resolved '{value}' -> '{chosen}' (searched project)",
            )

        return value, None

    def _autofix_params(
        self,
        params: Dict[str, str],
        invocation_cwd: str,
        task_cwd: Optional[str],
    ) -> Tuple[Dict[str, str], List[str]]:
        if not self._path_autofix_enabled():
            return params, []

        fixed = dict(params)
        warnings: List[str] = []
        for k, v in fixed.items():
            new_v, warn = self._autofix_path_value(k, v, invocation_cwd, task_cwd)
            if warn and new_v != v:
                warnings.append(warn)
                fixed[k] = new_v

        return fixed, warnings

    def _path_autofix_roots(self, invocation_cwd: str, task_cwd: Optional[str]) -> List[str]:
        roots: List[str] = []
        for root in (task_cwd, getattr(pf_parser_module, "PFY_ROOT", None), invocation_cwd):
            if root and os.path.isdir(root):
                root_abs = os.path.abspath(root)
                if root_abs not in roots:
                    roots.append(root_abs)
        return roots

    def _resolve_path_for_command(
        self,
        raw_path: str,
        invocation_cwd: str,
        task_cwd: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve a (possibly relative) path used inside a shell command.

        Unlike parameter autofix, prefer the task file directory first to preserve the
        "task runs from its own Pfyfile" rule. Falls back to project-wide search.
        """
        if not raw_path or not self._looks_like_path(raw_path):
            return None, None

        expanded = os.path.expanduser(os.path.expandvars(raw_path))
        if "$" in expanded:
            return None, None

        if os.path.isabs(expanded):
            return (expanded, None) if os.path.exists(expanded) else (None, None)

        roots = self._path_autofix_roots(invocation_cwd, task_cwd)
        for root in roots:
            candidate = os.path.abspath(os.path.join(root, expanded))
            if os.path.exists(candidate):
                return (
                    candidate,
                    f"resolved '{raw_path}' -> '{candidate}' (relative to {root})",
                )

        # Last resort: search for a matching basename under roots.
        basename = os.path.basename(expanded.rstrip("/\\"))
        if not basename:
            return None, None

        skip_dirs = {
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
            "target",
        }

        matches: List[str] = []
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in skip_dirs]
                if basename in dirnames:
                    matches.append(os.path.join(dirpath, basename))
                if basename in filenames:
                    matches.append(os.path.join(dirpath, basename))
                if len(matches) > 25:
                    break
            if len(matches) > 25:
                break

        if not matches:
            return None, None

        tail = os.path.normpath(expanded).replace("\\", "/")
        suffix_matches = [m for m in matches if m.replace("\\", "/").endswith(tail)]
        if len(suffix_matches) == 1:
            chosen = os.path.abspath(suffix_matches[0])
            return (
                chosen,
                f"resolved '{raw_path}' -> '{chosen}' (searched project for suffix match)",
            )

        if len(matches) == 1:
            chosen = os.path.abspath(matches[0])
            return (
                chosen,
                f"resolved '{raw_path}' -> '{chosen}' (searched project)",
            )

        return None, None

    def _extract_relative_shell_paths(self, script_text: str) -> List[str]:
        """
        Best-effort extraction of relative paths from shell scripts.

        This is intentionally heuristic: it targets the most common failure modes
        (e.g. `source ./helpers.sh`) without trying to fully parse shell syntax.
        """
        rel_paths: List[str] = []

        patterns = [
            # source ./file.sh / . ./file.sh
            r"(?:^|\s)(?:source|\.)\s+(['\"]?)([^'\"\s;|&()]+)\1",
            # cd ./dir
            r"(?:^|\s)cd\s+(['\"]?)([^'\"\s;|&()]+)\1",
            # bash ./file.sh / sh ./file.sh
            r"(?:^|\s)(?:bash|sh|zsh|fish)\s+(['\"]?)([^'\"\s;|&()]+)\1",
            # direct execution: ./script.sh
            r"(?:^|\s)(\./[^'\"\s;|&()]+)",
        ]

        for pat in patterns:
            for m in re.finditer(pat, script_text, flags=re.MULTILINE):
                g1 = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
                g2 = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
                p = (g2 or g1 or "").strip()
                if not p:
                    continue
                if p.startswith("-"):
                    continue
                if "$" in p or "`" in p:
                    continue
                if os.path.isabs(p):
                    continue
                if p in {".", ".."}:
                    continue
                rel_paths.append(p)

        # Generic pass: grab obvious relative path tokens used anywhere in the script.
        # This helps when the failure is e.g. `cat configs/foo.txt` rather than `source ...`.
        for line in script_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                toks = shlex.split(line, posix=True)
            except ValueError:
                continue
            for tok in toks:
                if not tok:
                    continue
                if tok.startswith(("-", "$")):
                    continue
                if "$" in tok or "`" in tok:
                    continue
                if "=" in tok:
                    continue
                if not self._looks_like_path(tok):
                    continue
                if os.path.isabs(tok):
                    continue
                if tok in {".", ".."}:
                    continue
                rel_paths.append(tok)

        # De-dupe while preserving order
        seen = set()
        out: List[str] = []
        for p in rel_paths:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out

    def _choose_cwd_for_script(
        self,
        script_abs: str,
        candidate_cwds: List[str],
        task_cwd: Optional[str],
    ) -> Optional[str]:
        if not script_abs or not os.path.isfile(script_abs):
            return None

        try:
            with open(script_abs, "r", encoding="utf-8", errors="ignore") as fh:
                script_text = fh.read(256 * 1024)
        except Exception:
            return None

        rel_paths = self._extract_relative_shell_paths(script_text)
        if not rel_paths:
            return None

        best = None
        best_score = -1
        best_task_preference = False

        for cwd in candidate_cwds:
            score = 0
            for p in rel_paths:
                if os.path.exists(os.path.join(cwd, p)):
                    score += 1

            task_pref = bool(task_cwd and os.path.abspath(cwd) == os.path.abspath(task_cwd))
            if score > best_score or (score == best_score and task_pref and not best_task_preference):
                best = cwd
                best_score = score
                best_task_preference = task_pref

        # Only change cwd when we have a strong signal.
        if best_score <= 0:
            return None
        return best

    def _reconstruct_shell_command(self, original_content: str, tokens: List[str], modified_indices: set) -> str:
        """
        Reconstruct a shell command line, preserving shell syntax while updating specific tokens.
        
        This avoids the shlex.split() -> modify -> shlex.join() pattern that incorrectly quotes
        shell metacharacters like [, ], (, ), &&, ||, etc.
        
        The key insight: we only quote the modified path tokens that need quoting (paths with
        special characters), and leave all other tokens as-is to preserve shell syntax.
        
        Note: This approach joins tokens with single spaces, which may differ from the original
        spacing. This is acceptable because:
        - Shell commands treat multiple spaces the same as single spaces (except in quoted strings)
        - We only modify path tokens, not quoted strings
        - The alternative (shlex.join) would break shell syntax entirely
        
        Args:
            original_content: The original command line string; returned unchanged if no modifications
            tokens: List of tokens (from shlex.split)
            modified_indices: Set of indices of tokens that were modified
            
        Returns:
            Reconstructed command string with modified tokens replaced
        """
        if not modified_indices:
            return original_content
        
        # Reconstruct by joining tokens, but only quote modified tokens if they need it
        result_parts = []
        for idx, tok in enumerate(tokens):
            if idx in modified_indices:
                # This token was modified (typically a path that was resolved)
                # Quote it if it contains shell metacharacters that would break parsing
                if self._needs_shell_quoting(tok):
                    result_parts.append(shlex.quote(tok))
                else:
                    # For simple absolute paths without special characters, no quoting needed
                    result_parts.append(tok)
            else:
                # Original token - keep as-is without quoting
                # This preserves shell operators like [, ], &&, ||, (, ), etc.
                result_parts.append(tok)
        
        # Join with spaces. This loses information about original spacing but preserves
        # shell syntax since we're not quoting the shell operators.
        return ' '.join(result_parts)

    def _maybe_generate_corrected_shell_script(
        self, script_abs: str, invocation_cwd: str, task_cwd: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a corrected copy of a shell script that rewrites common relative-path
        pitfalls (e.g. `source ./helpers.sh`) to absolute paths based on the script's
        own directory.

        This keeps the "task cwd is the base" rule while making scripts more robust.
        """
        if not script_abs or not os.path.isfile(script_abs):
            return None, None

        try:
            st = os.stat(script_abs)
        except OSError:
            return None, None

        try:
            with open(script_abs, "r", encoding="utf-8", errors="ignore") as fh:
                original_text = fh.read(512 * 1024)
        except Exception:
            return None, None

        first_line = original_text.splitlines()[0] if original_text else ""
        is_shell = False
        if script_abs.lower().endswith((".sh", ".bash", ".zsh", ".fish")):
            is_shell = True
        if first_line.startswith("#!") and any(x in first_line for x in ("sh", "bash", "zsh", "fish", "dash", "ksh")):
            is_shell = True
        if not is_shell:
            return None, None

        script_dir = os.path.dirname(os.path.abspath(script_abs))
        roots = self._path_autofix_roots(invocation_cwd, task_cwd)

        def _resolve_rel(p: str) -> Optional[str]:
            if not p or os.path.isabs(p) or "$" in p or "`" in p:
                return None
            # Prefer the script's own directory first (most common expectation).
            cand = os.path.abspath(os.path.join(script_dir, p))
            if os.path.exists(cand):
                return cand
            # Fall back to the standard roots (task cwd / project root / invocation cwd).
            for r in roots:
                cand2 = os.path.abspath(os.path.join(r, p))
                if os.path.exists(cand2):
                    return cand2
            return None

        changed = False
        out_lines: List[str] = []

        for line in original_text.splitlines(keepends=True):
            newline = "\n" if line.endswith("\n") else ""
            body = line[:-1] if newline else line

            indent_len = len(body) - len(body.lstrip(" \t"))
            indent = body[:indent_len]
            content = body[indent_len:]

            stripped = content.strip()
            if not stripped or stripped.startswith("#"):
                out_lines.append(line)
                continue

            try:
                toks = shlex.split(content, posix=True)
            except ValueError:
                out_lines.append(line)
                continue

            if not toks:
                out_lines.append(line)
                continue

            local_changed = False
            modified_indices = set()  # Track which token indices were modified
            op_tokens = {"&&", "||", ";", "|", "&", "(", ")", "{", "}"}
            env_assign_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")

            at_command_start = True
            idx = 0
            while idx < len(toks):
                tok = toks[idx]
                if tok in op_tokens:
                    at_command_start = True
                    idx += 1
                    continue

                if at_command_start:
                    # Skip leading KEY=value env assignments before a command.
                    if env_assign_re.match(tok) and not tok.startswith("-"):
                        idx += 1
                        continue

                    # `source ./x` / `. ./x`
                    if tok in {"source", "."} and idx + 1 < len(toks):
                        resolved = _resolve_rel(toks[idx + 1])
                        if resolved:
                            toks[idx + 1] = resolved
                            modified_indices.add(idx + 1)
                            local_changed = True
                        at_command_start = False
                        idx += 1
                        continue

                    # `bash ./x` etc (only when used as a command, not as an argument).
                    if tok in {"bash", "sh", "zsh", "fish"} and idx + 1 < len(toks):
                        if not toks[idx + 1].startswith("-"):
                            resolved = _resolve_rel(toks[idx + 1])
                            if resolved:
                                toks[idx + 1] = resolved
                                modified_indices.add(idx + 1)
                                local_changed = True
                        at_command_start = False
                        idx += 1
                        continue

                    # Direct execution: `./script.sh` / `../tool`
                    if tok.startswith(("./", "../")):
                        resolved = _resolve_rel(tok)
                        if resolved:
                            toks[idx] = resolved
                            modified_indices.add(idx)
                            local_changed = True

                    at_command_start = False

                idx += 1

            if local_changed:
                changed = True
                out_lines.append(indent + self._reconstruct_shell_command(content, toks, modified_indices) + newline)
            else:
                out_lines.append(line)

        if not changed:
            return None, None

        header = [
            f"# pf-path-autofix: {script_abs}\n",
            f"# original-mtime: {st.st_mtime}\n",
            f"# original-size: {st.st_size}\n",
        ]
        corrected_text = "".join(header) + "".join(out_lines)

        write_next_to_script = pf_config.get_bool(
            self.config or {}, "runner.pathAutofixWriteCorrectedNextToScript", False
        )

        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "pf", "corrected")
        digest = hashlib.sha256(script_abs.encode("utf-8")).hexdigest()[:12]
        base = os.path.basename(script_abs)
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
        cache_path = os.path.join(cache_dir, f"{safe}.{digest}.corrected")

        corrected_path = script_abs + ".corrected" if write_next_to_script else cache_path

        # Avoid rewriting on every run when the cached corrected script matches the input.
        try:
            if os.path.exists(corrected_path):
                with open(corrected_path, "r", encoding="utf-8", errors="ignore") as fh:
                    head = fh.read(4096)
                if f"# pf-path-autofix: {script_abs}\n" in head and f"# original-mtime: {st.st_mtime}\n" in head:
                    return corrected_path, f"using cached corrected script '{corrected_path}'"
        except Exception:
            pass

        try:
            os.makedirs(os.path.dirname(corrected_path), exist_ok=True)
            with open(corrected_path, "w", encoding="utf-8") as fh:
                fh.write(corrected_text)
            try:
                os.chmod(corrected_path, st.st_mode | 0o111)
            except Exception:
                pass
            note = "generated corrected script"
            if not write_next_to_script:
                note += " (cache)"
            return corrected_path, f"{note} '{corrected_path}'"
        except Exception:
            if write_next_to_script and corrected_path != cache_path:
                # Fall back to cache when we can't write next to the script.
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                    with open(cache_path, "w", encoding="utf-8") as fh:
                        fh.write(corrected_text)
                    try:
                        os.chmod(cache_path, st.st_mode | 0o111)
                    except Exception:
                        pass
                    return cache_path, f"generated corrected script '{cache_path}' (cache)"
                except Exception:
                    return None, None
            return None, None

    def _autofix_polyglot_file_ref(
        self,
        cmd: str,
        invocation_cwd: str,
        task_cwd: Optional[str],
    ) -> Tuple[str, List[str]]:
        """
        If the command starts with @file / file:file, resolve it to an absolute path.
        """
        if not cmd.strip():
            return cmd, []
        try:
            tokens = shlex.split(cmd, posix=True)
        except ValueError:
            return cmd, []
        if not tokens:
            return cmd, []

        tok0 = tokens[0]
        prefix = None
        path_part = None
        if tok0.startswith("@") and len(tok0) > 1:
            prefix = "@"
            path_part = tok0[1:]
        elif tok0.startswith("file:") and len(tok0) > 5:
            prefix = "file:"
            path_part = tok0[5:]

        if not prefix or not path_part:
            return cmd, []

        resolved, note = self._resolve_path_for_command(path_part, invocation_cwd, task_cwd)
        if not resolved:
            return cmd, []

        tokens[0] = f"{prefix}{resolved}"
        warnings = []
        if note:
            warnings.append(f"polyglot source {note}")
        
        # Polyglot file references are in the form @file or file:file
        # We only modify the first token (the file path), so track that
        modified_indices = {0}
        
        # For single-token commands, check if quoting is needed
        if len(tokens) == 1:
            tok = tokens[0]
            # Quote if the token contains shell metacharacters
            if self._needs_shell_quoting(tok):
                return shlex.quote(tok), warnings
            else:
                return tok, warnings
        else:
            # Multiple tokens - reconstruct preserving shell syntax
            return self._reconstruct_shell_command(cmd, tokens, modified_indices), warnings

    def _autofix_shell_command_context(
        self,
        cmd: str,
        invocation_cwd: str,
        task_cwd: Optional[str],
    ) -> Tuple[str, Optional[str], List[str]]:
        """
        Best-effort: fix common path mistakes for script-style commands.

        Returns:
          (possibly rewritten_cmd, cwd_override, warnings)
        """
        if not self._path_autofix_enabled():
            return cmd, None, []
        if not cmd.strip():
            return cmd, None, []
        if "\n" in cmd:
            # Multi-line scripts are opaque; prefer task_cwd.
            return cmd, None, []

        try:
            tokens = shlex.split(cmd, posix=True)
        except ValueError:
            return cmd, None, []

        if not tokens:
            return cmd, None, []

        # Skip leading KEY=value env assignments.
        start = 0
        env_key_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
        while start < len(tokens):
            t = tokens[start]
            if env_key_re.match(t) and not t.startswith("-"):
                start += 1
                continue
            break
        if start >= len(tokens):
            return cmd, None, []

        runner = tokens[start]

        def _is_command_string_flag(flag: str) -> bool:
            return flag in {"-c", "-lc"} or flag.endswith("c") and flag.startswith("-") and "c" in flag

        script_idx = None
        script_ref = None

        if runner in {"bash", "sh", "zsh", "fish", "dash", "ksh", "tcsh"}:
            j = start + 1
            while j < len(tokens) and tokens[j].startswith("-"):
                if _is_command_string_flag(tokens[j]):
                    # `bash -lc "..."` etc; can't safely rewrite.
                    return cmd, None, []
                j += 1
            if j < len(tokens):
                script_idx = j
                script_ref = tokens[j]
        elif runner in {"python", "python3", "python2", "node", "deno", "ruby", "perl", "php", "lua", "pwsh", "powershell"}:
            j = start + 1
            while j < len(tokens) and tokens[j].startswith("-"):
                if tokens[j] in {"-c", "-m", "-e"}:
                    return cmd, None, []
                j += 1
            if runner == "deno" and j < len(tokens) and tokens[j] == "run":
                j += 1
                while j < len(tokens) and tokens[j].startswith("-"):
                    j += 1
            if j < len(tokens):
                script_idx = j
                script_ref = tokens[j]
        elif runner in {".", "source"}:
            if start + 1 < len(tokens):
                script_idx = start + 1
                script_ref = tokens[script_idx]
        else:
            # Direct execution of a file-like token.
            if self._looks_like_path(runner) and not runner.startswith("$"):
                script_idx = start
                script_ref = runner

        if script_idx is None or not script_ref:
            return cmd, None, []

        # Ignore obvious non-path tokens and interpolation.
        if script_ref.startswith(("-", "$")) or "$" in script_ref or "`" in script_ref:
            return cmd, None, []

        resolved, note = self._resolve_path_for_command(script_ref, invocation_cwd, task_cwd)
        if not resolved:
            return cmd, None, []

        warnings: List[str] = []
        if note:
            warnings.append(f"script path {note}")

        corrected, corr_note = self._maybe_generate_corrected_shell_script(
            resolved, invocation_cwd, task_cwd
        )
        if corrected:
            tokens[script_idx] = corrected
            if corr_note:
                warnings.append(corr_note)
            modified_indices = {script_idx}
            return self._reconstruct_shell_command(cmd, tokens, modified_indices), None, warnings

        # Prefer running from the task file directory unless the script strongly
        # indicates it expects a different base.
        candidates: List[str] = []
        for c in (
            task_cwd,
            os.path.dirname(os.path.abspath(resolved)),
            os.path.abspath(getattr(pf_parser_module, "PFY_ROOT", invocation_cwd) or invocation_cwd),
            os.path.abspath(invocation_cwd),
        ):
            if c and os.path.isdir(c):
                c_abs = os.path.abspath(c)
                if c_abs not in candidates:
                    candidates.append(c_abs)

        cwd_override = self._choose_cwd_for_script(resolved, candidates, task_cwd)

        # Always rewrite the script token to an absolute path so the command still
        # works when we adjust cwd.
        tokens[script_idx] = resolved
        if cwd_override and task_cwd and os.path.abspath(cwd_override) != os.path.abspath(task_cwd):
            warnings.append(
                f"running script from '{cwd_override}' instead of task cwd '{task_cwd}' (relative paths in script)"
            )

        modified_indices = {script_idx}
        return self._reconstruct_shell_command(cmd, tokens, modified_indices), cwd_override, warnings
    
    def _execute_on_hosts(self, selected_tasks: List[Tuple[str, List[str], Dict[str, str], Optional[str]]], 
                         hosts: List[str], args) -> int:
        """Execute tasks on the specified hosts."""

        invocation_cwd = os.getcwd()
        
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
            for task_name, lines, params, source_file in selected_tasks:
                task_cwd = self._task_cwd_for(source_file)
                print(f"{prefix} --> {task_name}")
                task_env: Dict[str, str] = {}
                shell_lang: Optional[str] = None

                effective_params = dict(params)
                if connection is None:
                    effective_params, warnings = self._autofix_params(
                        effective_params, invocation_cwd, task_cwd
                    )
                    for w in warnings:
                        print(f"{prefix}[warn] {task_name}: {w}", file=sys.stderr)

                # Expose task params as environment variables so shell features like
                # `${param:-default}` work without relying on external env-var config.
                for k, v in effective_params.items():
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(k)):
                        task_env[str(k)] = str(v)

                pfy_root = getattr(pf_parser_module, "PFY_ROOT", None) or invocation_cwd
                if pfy_root:
                    task_env.setdefault("PFY_ROOT", str(pfy_root))
                if source_file:
                    task_env.setdefault("PF_TASK_FILE", str(source_file))
                    task_env.setdefault(
                        "PF_TASK_DIR",
                        os.path.dirname(os.path.abspath(source_file)) or str(pfy_root),
                    )
                elif task_cwd:
                    task_env.setdefault("PF_TASK_DIR", str(task_cwd))
                
                for line in lines:
                    stripped = line.strip()
                    
                    # Handle env command (stateful)
                    if stripped.startswith('env '):
                        for tok in shlex.split(stripped)[1:]:
                            if '=' in tok:
                                k, v = tok.split('=', 1)
                                task_env[k] = _interpolate(v, effective_params, task_env)
                        continue

                    # Handle shell language directive (stateful)
                    if stripped == "shell_lang" or stripped.startswith("shell_lang "):
                        lang = stripped[len("shell_lang"):].strip()
                        lang = lang.lstrip()
                        if not lang or lang.lower() in {"default", "none"}:
                            shell_lang = None
                        else:
                            shell_lang = lang
                        continue
                    
                    try:
                        # Flexible syntax: all non-directive lines are treated as shell commands.
                        # The explicit `shell ...` verb remains supported but is optional.
                        shell_cmd = stripped
                        if shell_cmd.startswith("shell "):
                            shell_cmd = shell_cmd[6:].strip()

                        shell_cmd = _interpolate(shell_cmd, effective_params, task_env)

                        lang_hint = shell_lang
                        m = _LANG_BRACKET_RE.match(shell_cmd)
                        if m:
                            lang_hint = m.group(1).strip()
                            shell_cmd = m.group(2)

                        output_path = None
                        cmd_cwd = task_cwd

                        if self._path_autofix_enabled():
                            if lang_hint:
                                # Polyglot @file paths are resolved locally even when running on remote hosts.
                                shell_cmd, fixes = self._autofix_polyglot_file_ref(
                                    shell_cmd, invocation_cwd, task_cwd
                                )
                                for f in fixes:
                                    print(f"{prefix}[warn] {task_name}: {f}", file=sys.stderr)
                            elif connection is None:
                                shell_cmd, cwd_override, fixes = self._autofix_shell_command_context(
                                    shell_cmd, invocation_cwd, task_cwd
                                )
                                if cwd_override:
                                    cmd_cwd = cwd_override
                                for f in fixes:
                                    print(f"{prefix}[warn] {task_name}: {f}", file=sys.stderr)

                        if lang_hint:
                            heredoc = _extract_polyglot_heredoc(shell_cmd)
                            if heredoc:
                                shell_cmd, output_path = heredoc

                            rendered, _ = render_polyglot_command(lang_hint, shell_cmd, task_cwd)
                            if rendered:
                                shell_cmd = rendered

                            if output_path:
                                shell_cmd = f"(\n{shell_cmd}\n) > {shlex.quote(output_path)}"

                        rc = execute_shell_command(
                            shell_cmd,
                            task_env,
                            args.sudo,
                            args.sudo_user,
                            connection,
                            prefix,
                            cwd=cmd_cwd,
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
