#!/usr/bin/env python3
"""
pf_task_executor.py - Task execution orchestration for pf

This module provides:
- Task execution coordination
- Remote execution management
- Parallel task execution
- Error handling and reporting

Extracted from pf_main.py to follow Single Responsibility Principle.
"""

import sys
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing pf functionality
from pf_parser import (
    _find_pfyfile, _load_pfy_source_with_includes, parse_pfyfile_text,
    get_alias_map, run_task_by_name
)
from pf_exceptions import PFException, format_exception_for_user


class TaskExecutor:
    """Handles task execution orchestration."""
    
    def __init__(self):
        pass

    def _build_cli_args(self, args, command_tokens: List[str]) -> List[str]:
        """Reconstruct CLI args so execution uses the main runner path."""
        cli_args: List[str] = []

        file_arg = getattr(args, "file", None)
        if file_arg:
            cli_args.extend(["--file", file_arg])

        for env_name in getattr(args, "env", []) or []:
            cli_args.extend(["--env", env_name])

        hosts = getattr(args, "hosts", None) or []
        if isinstance(hosts, str):
            hosts = [hosts]
        for host_group in hosts:
            cli_args.extend(["--hosts", host_group])

        host_values = getattr(args, "host", None) or []
        if isinstance(host_values, str):
            host_values = [host_values]
        for host in host_values:
            cli_args.extend(["--host", host])

        user = getattr(args, "user", None)
        if user:
            cli_args.extend(["--user", user])

        port = getattr(args, "port", None)
        if port is not None:
            cli_args.extend(["--port", str(port)])

        if getattr(args, "sudo", False):
            cli_args.append("--sudo")

        sudo_user = getattr(args, "sudo_user", None)
        if sudo_user:
            cli_args.extend(["--sudo-user", sudo_user])

        cli_args.extend(command_tokens)
        return cli_args
    
    def handle_run_command(self, args) -> int:
        """Handle the run command."""
        from pf_main import main as pf_main_entry

        command_tokens = ["run", args.task, *(getattr(args, "task_args", []) or [])]
        return pf_main_entry(self._build_cli_args(args, command_tokens))
    
    def handle_subcommand(self, args) -> int:
        """Handle subcommand execution."""
        # Extract the subcommand name from the args
        subcommand = (
            getattr(args, "subcommand", None)
            or getattr(args, "command", None)
        )
        
        if not subcommand:
            print("No subcommand specified.", file=sys.stderr)
            return 1

        from pf_main import main as pf_main_entry

        command_tokens = [subcommand, args.task, *(getattr(args, "params", []) or [])]
        return pf_main_entry(self._build_cli_args(args, command_tokens))
    
    def execute_parallel_tasks(self, tasks: List[Dict], max_workers: int = 4) -> int:
        """Execute multiple tasks in parallel."""
        if not tasks:
            return 0
        
        rc_total = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {}
            for task_info in tasks:
                future = executor.submit(self._execute_single_task, task_info)
                future_to_task[future] = task_info
            
            # Collect results
            for future in as_completed(future_to_task):
                task_info = future_to_task[future]
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
    
    def _execute_single_task(self, task_info: Dict) -> int:
        """Execute a single task with the given parameters."""
        from types import SimpleNamespace
        from pf_main import main as pf_main_entry

        args = SimpleNamespace(
            file=task_info.get("file_arg"),
            env=task_info.get("env_arg"),
            hosts=task_info.get("hosts_arg"),
            host=task_info.get("host_arg"),
            user=task_info.get("user"),
            port=task_info.get("port"),
            sudo=task_info.get("sudo", False),
            sudo_user=task_info.get("sudo_user"),
        )
        command_tokens = [
            "run",
            task_info["task_name"],
            *(task_info.get("task_args", []) or []),
        ]
        return pf_main_entry(self._build_cli_args(args, command_tokens))