#!/usr/bin/env python3
"""
pf_args_help.py - Help/usage routing helpers for pf argument parsing.
"""

from __future__ import annotations

import argparse
from typing import List, Optional, Sequence, Set, Dict

# Help command variations - common typos and alternatives
HELP_VARIATIONS = {
    "help",
    "--help",
    "-h",
    "hlep",
    "hepl",
    "heelp",
    "hlp",
    "--hlep",
    "--hepl",
    "--heelp",
    "--hlp",
}


def route_help_args(
    args: Sequence[str],
    parser: argparse.ArgumentParser,
    subcommand_names: Set[str],
    subcommand_files: Dict[str, str],
) -> Optional[argparse.Namespace]:
    """Return a parsed Namespace for help-routing cases, or None."""
    args = list(args)

    if not args or args[0] in HELP_VARIATIONS:
        if len(args) > 1:
            return parser.parse_args(["help", args[1]])
        return parser.parse_args(["--help"])

    help_flags = set(HELP_VARIATIONS)

    if args[0] in subcommand_names and any(arg in help_flags for arg in args[1:]):
        task = None
        for arg in args[1:]:
            if arg in help_flags:
                break
            if arg.startswith("-") or "=" in arg:
                continue
            task = arg
            break
        if task:
            return parser.parse_args(["help", task])
        return parser.parse_args(args)

    if any(arg in help_flags for arg in args[1:]):
        value_opts = {
            "--config",
            "-f",
            "--file",
            "--env",
            "--hosts",
            "--host",
            "--user",
            "--port",
            "--sudo-user",
        }
        builtin_commands = {"list", "run", "help", "prune", "debug-on", "debug-off", "version"}

        def _help_args_with_subcommand_file(
            subcommand: str,
            topic: str,
            base_opts: List[str],
        ) -> List[str]:
            opts = list(base_opts)
            has_file = any(opt in ("--file", "-f") for opt in opts) or any(
                opt.startswith("--file=") for opt in opts
            )
            if not has_file:
                sub_file = subcommand_files.get(subcommand)
                if sub_file:
                    opts.extend(["--file", sub_file])
            return opts + ["help", topic]

        def _collect_global_opts(raw_args: List[str]) -> List[str]:
            opts: List[str] = []
            i = 0
            while i < len(raw_args):
                arg = raw_args[i]
                if arg in help_flags:
                    i += 1
                    continue
                if arg in value_opts:
                    if i + 1 < len(raw_args):
                        opts.extend([arg, raw_args[i + 1]])
                        i += 2
                        continue
                    i += 1
                    continue
                if arg == "--sudo":
                    opts.append(arg)
                    i += 1
                    continue
                if arg.startswith("--") and "=" in arg:
                    if any(
                        arg.startswith(prefix)
                        for prefix in (
                            "--config=",
                            "--file=",
                            "--env=",
                            "--hosts=",
                            "--host=",
                            "--user=",
                            "--port=",
                            "--sudo-user=",
                        )
                    ):
                        opts.append(arg)
                    i += 1
                    continue
                i += 1
            return opts

        global_opts = _collect_global_opts(args)

        positionals: List[str] = []
        skip_next = False
        for arg in args:
            if skip_next:
                skip_next = False
                continue
            if arg in help_flags:
                break
            if arg in value_opts:
                skip_next = True
                continue
            if arg.startswith("--") and "=" in arg:
                continue
            if arg.startswith("-"):
                continue
            if "=" in arg:
                continue
            positionals.append(arg)
            if len(positionals) >= 2:
                break

        candidate = positionals[0] if positionals else None
        candidate_next = positionals[1] if len(positionals) > 1 else None

        if candidate:
            if candidate == "run" and candidate_next:
                return parser.parse_args(global_opts + ["help", candidate_next])
            if candidate in subcommand_names and not candidate_next:
                return parser.parse_args(args)
            if candidate not in builtin_commands:
                if candidate in subcommand_names and candidate_next:
                    return parser.parse_args(
                        _help_args_with_subcommand_file(candidate, candidate_next, global_opts)
                    )
                if candidate_next and "=" not in candidate_next:
                    return parser.parse_args(global_opts + ["help", candidate_next])
                return parser.parse_args(global_opts + ["help", candidate])

    if len(args) > 1 and args[1] in HELP_VARIATIONS and not args[0].startswith("-"):
        builtin_commands = {
            "list",
            "run",
            "help",
            "prune",
            "debug-on",
            "debug-off",
            "version",
        }
        if args[0] not in builtin_commands and args[0] not in subcommand_names:
            global_opts: List[str] = []
            i = 0
            while i < len(args):
                arg = args[i]
                if arg in help_flags:
                    i += 1
                    continue
                if arg in (
                    "--config",
                    "-f",
                    "--file",
                    "--env",
                    "--hosts",
                    "--host",
                    "--user",
                    "--port",
                    "--sudo-user",
                ):
                    if i + 1 < len(args):
                        global_opts.extend([arg, args[i + 1]])
                        i += 2
                        continue
                    i += 1
                    continue
                if arg == "--sudo":
                    global_opts.append(arg)
                    i += 1
                    continue
                if arg.startswith("--") and "=" in arg:
                    global_opts.append(arg)
                    i += 1
                    continue
                i += 1
            return parser.parse_args(global_opts + ["help", args[0]])

    return None
