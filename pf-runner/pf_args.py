#!/usr/bin/env python3
"""
pf_args.py - Enhanced argument parsing for pf with subcommand support

This module provides:
- Proper argparse-based argument parsing
- Subcommand architecture
- Auto-discovery of subcommands from included files
- Backward compatibility with existing usage patterns
- Flexible help command support (help, -h, --help, hlep, hepl, heelp, hlp)
- Flexible parameter formats (--key=value, -k val, key=value)
"""

import argparse
import os
import sys
from typing import List, Dict, Optional, Tuple, Any
import re

# Help command variations - common typos and alternatives
HELP_VARIATIONS = {"help", "--help", "-h", "hlep", "hepl", "heelp", "hlp"}


class PfArgumentParser:
    """Enhanced argument parser for pf with subcommand support."""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog="pf",
            description="pf - single-file, symbol-free Fabric runner with a tiny DSL",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  pf list                           # List all available tasks
  pf run task_name                  # Run a task locally
  pf run task_name env=prod         # Run task on prod environment
  pf run task_name hosts=server1,server2  # Run on specific hosts
  pf web dev                        # Run dev task from web subcommand
  pf lifting install-tools          # Run install-tools from lifting subcommand
  
Environment Variables:
  PFY_FILE                          # Override default Pfyfile.pf location
  
For more help on a specific subcommand:
  pf <subcommand> --help
            """,
        )

        # Global options that apply to all subcommands
        self.parser.add_argument(
            "-f", "--file", help="Specify Pfyfile location (default: Pfyfile.pf)"
        )
        self.parser.add_argument(
            "--env",
            action="append",
            help="Environment name(s) to use for host resolution",
        )
        self.parser.add_argument(
            "--hosts", help="Comma-separated list of hosts (user@host:port)"
        )
        self.parser.add_argument(
            "--host", action="append", help="Single host (can be repeated)"
        )
        self.parser.add_argument("--user", help="Default SSH user")
        self.parser.add_argument("--port", help="Default SSH port")
        self.parser.add_argument(
            "--sudo", action="store_true", help="Run commands with sudo"
        )
        self.parser.add_argument(
            "--sudo-user", help="Run commands as specific sudo user"
        )

        # Create subparsers
        self.subparsers = self.parser.add_subparsers(
            dest="command", help="Available commands", metavar="COMMAND"
        )

        # Add built-in commands
        self._add_builtin_commands()

    def _add_builtin_commands(self):
        """Add built-in pf commands."""

        # list command
        list_parser = self.subparsers.add_parser(
            "list",
            help="List available tasks",
            description="List all available tasks with descriptions",
        )
        list_parser.add_argument(
            "--subcommand", help="Show tasks only from specific subcommand"
        )

        # run command (default)
        run_parser = self.subparsers.add_parser(
            "run",
            help="Run tasks (default command)",
            description="Run one or more tasks with optional parameters",
        )
        run_parser.add_argument(
            "tasks",
            nargs="+",
            help="Task name(s) and parameters (task param=value next_task ...)",
        )

        # help command
        help_parser = self.subparsers.add_parser(
            "help",
            help="Show help for tasks or subcommands",
            description="Show detailed help for specific tasks or subcommands",
        )
        help_parser.add_argument(
            "topic", nargs="?", help="Task or subcommand to show help for"
        )

        # prune command - syntax checking
        prune_parser = self.subparsers.add_parser(
            "prune",
            help="Check syntax of tasks and report errors",
            description="Validate all tasks for syntax errors without executing them",
        )
        prune_parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="Only check syntax, do not execute (default behavior)",
        )
        prune_parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Show verbose output with stack traces",
        )
        prune_parser.add_argument(
            "-o",
            "--output",
            default="pfail.fail.pf",
            help="Output file for failed tasks (default: pfail.fail.pf)",
        )

        # debug-on command
        debug_on_parser = self.subparsers.add_parser(
            "debug-on",
            help="Enable debug mode for verbose error reporting",
            description="Toggle debug mode on - provides full stack traces for errors",
        )

        # debug-off command
        debug_off_parser = self.subparsers.add_parser(
            "debug-off",
            help="Disable debug mode",
            description="Toggle debug mode off - returns to normal error reporting",
        )

    def add_subcommand_from_file(self, filename: str, tasks: List[str]):
        """Add a subcommand based on an included file."""
        # Transform filename to subcommand name
        # e.g., "Pfyfile.web-demo.pf" -> "web-demo"
        # e.g., "Pfyfile.build_helpers.pf" -> "build-helpers"
        basename = os.path.basename(filename)
        if basename.startswith("Pfyfile.") and basename.endswith(".pf"):
            subcommand_name = basename[8:-3]  # Remove "Pfyfile." and ".pf"
            subcommand_name = subcommand_name.replace("_", "-").lower()

            # Don't create subcommand for main Pfyfile
            if subcommand_name in ("", "pf"):
                return

            # Create subcommand parser
            subparser = self.subparsers.add_parser(
                subcommand_name,
                help=f"Tasks from {basename}",
                description=f"Run tasks defined in {basename}",
            )
            subparser.add_argument("task", help="Task name to run")
            subparser.add_argument(
                "params", nargs="*", help="Task parameters (key=value)"
            )

            # Store task list for this subcommand
            subparser.set_defaults(subcommand_tasks=tasks, subcommand_file=filename)

    def parse_legacy_args(
        self, args: List[str]
    ) -> Tuple[argparse.Namespace, List[str]]:
        """Parse arguments with backward compatibility for legacy syntax."""

        # Handle legacy syntax where first arg might be a file
        if args and not args[0].startswith("-") and "=" not in args[0]:
            if os.path.exists(args[0]) or args[0].endswith(".pf"):
                # First arg is a file
                file_arg = args[0]
                remaining_args = args[1:]
            else:
                file_arg = None
                remaining_args = args
        else:
            file_arg = None
            remaining_args = args

        # Separate legacy key=value pairs from task arguments
        legacy_params = []
        task_args = []

        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]

            # Check for legacy key=value syntax (not starting with --)
            if "=" in arg and not arg.startswith("--"):
                key, value = arg.split("=", 1)
                if key in (
                    "env",
                    "hosts",
                    "host",
                    "user",
                    "port",
                    "sudo",
                    "sudo_user",
                    "become",
                    "become_user",
                ):
                    legacy_params.append(arg)
                    i += 1
                    continue

            # Everything else goes to task args
            task_args.extend(remaining_args[i:])
            break

        # Convert legacy params to modern format
        modern_args = []
        if file_arg:
            modern_args.extend(["--file", file_arg])

        for param in legacy_params:
            key, value = param.split("=", 1)
            if key == "env":
                modern_args.extend(["--env", value])
            elif key == "hosts":
                modern_args.extend(["--hosts", value])
            elif key == "host":
                modern_args.extend(["--host", value])
            elif key == "user":
                modern_args.extend(["--user", value])
            elif key == "port":
                modern_args.extend(["--port", value])
            elif key in ("sudo", "become"):
                if value.lower() in ("1", "true", "yes", "on"):
                    modern_args.append("--sudo")
            elif key in ("sudo_user", "become_user"):
                modern_args.extend(["--sudo-user", value])

        # If no explicit command and we have task args, assume 'run'
        if task_args and task_args[0] not in ("list", "help", "run"):
            # Check if first arg looks like a subcommand
            potential_subcommand = task_args[0]
            if (
                hasattr(self, "_subcommand_names")
                and potential_subcommand in self._subcommand_names
            ):
                # It's a subcommand
                modern_args.extend(task_args)
            else:
                # It's a task for the run command
                modern_args.append("run")
                modern_args.extend(task_args)
        else:
            modern_args.extend(task_args)

        return modern_args

    def parse_args(self, args: List[str]) -> argparse.Namespace:
        """Parse arguments with legacy compatibility."""

        # Handle special cases for backward compatibility
        # Support help variations: help, --help, -h, hlep, hepl, heelp, hlp
        if not args or args[0] in HELP_VARIATIONS:
            if len(args) > 1:
                # Help for specific topic
                return self.parser.parse_args(["help", args[1]])
            else:
                return self.parser.parse_args(["--help"])

        if args[0] == "list":
            return self.parser.parse_args(args)

        # Convert legacy syntax to modern
        modern_args = self.parse_legacy_args(args)

        try:
            return self.parser.parse_args(modern_args)
        except SystemExit:
            # If parsing fails, try legacy fallback
            return self._parse_legacy_fallback(args)

    def _parse_legacy_fallback(self, args: List[str]) -> argparse.Namespace:
        """Fallback parser for complete legacy compatibility."""

        # Create a minimal namespace with legacy parsing
        namespace = argparse.Namespace()
        namespace.command = "run"
        namespace.file = None
        namespace.env = []
        namespace.hosts = None
        namespace.host = []
        namespace.user = None
        namespace.port = None
        namespace.sudo = False
        namespace.sudo_user = None
        namespace.tasks = []

        # Parse legacy format manually
        i = 0
        if args and (os.path.exists(args[0]) or args[0].endswith(".pf")):
            namespace.file = args[0]
            i = 1

        # Parse key=value pairs
        while i < len(args):
            arg = args[i]
            if "=" in arg and not arg.startswith("--"):
                key, value = arg.split("=", 1)
                if key == "env":
                    namespace.env.append(value)
                elif key == "hosts":
                    namespace.hosts = value
                elif key == "host":
                    namespace.host.append(value)
                elif key == "user":
                    namespace.user = value
                elif key == "port":
                    namespace.port = value
                elif key in ("sudo", "become"):
                    namespace.sudo = value.lower() in ("1", "true", "yes", "on")
                elif key in ("sudo_user", "become_user"):
                    namespace.sudo_user = value
                else:
                    # This is a task parameter
                    namespace.tasks.extend(args[i:])
                    break
            else:
                # Rest are tasks
                namespace.tasks.extend(args[i:])
                break
            i += 1

        return namespace


def create_pfuck_parser() -> argparse.ArgumentParser:
    """Create argument parser for pfuck command."""

    parser = argparse.ArgumentParser(
        prog="pfuck",
        description="pfuck - autocorrect failed pf tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pfuck                             # Suggest correction for last failed command
  pfuck "pf run web-dve"           # Suggest correction for specific command
  pfuck --list                     # List all available tasks for reference
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="Failed command to correct (if not provided, uses last failed command)",
    )
    parser.add_argument("--list", action="store_true", help="List all available tasks")
    parser.add_argument("--file", "-f", help="Pfyfile to use for task discovery")
    parser.add_argument(
        "--execute",
        "-e",
        action="store_true",
        help="Execute the suggested correction automatically",
    )

    return parser
