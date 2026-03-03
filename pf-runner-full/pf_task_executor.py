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
    
    def handle_run_command(self, args) -> int:
        """Handle the run command."""
        return run_task_by_name(
            task_name=args.task,
            file_arg=args.file,
            hosts_arg=args.hosts,
            env_arg=args.env,
            dry_run=args.dry_run,
            debug=args.debug,
            parallel=args.parallel,
            task_args=getattr(args, 'task_args', [])
        )
    
    def handle_subcommand(self, args) -> int:
        """Handle subcommand execution."""
        # Extract the subcommand name from the args
        subcommand = args.subcommand if hasattr(args, 'subcommand') else None
        
        if not subcommand:
            print("No subcommand specified.", file=sys.stderr)
            return 1
        
        # Run the subcommand as a task
        return run_task_by_name(
            task_name=subcommand,
            file_arg=args.file,
            hosts_arg=args.hosts,
            env_arg=args.env,
            dry_run=args.dry_run,
            debug=args.debug,
            parallel=args.parallel,
            task_args=getattr(args, 'task_args', [])
        )
    
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
        return run_task_by_name(
            task_name=task_info['task_name'],
            file_arg=task_info.get('file_arg'),
            hosts_arg=task_info.get('hosts_arg'),
            env_arg=task_info.get('env_arg'),
            dry_run=task_info.get('dry_run', False),
            debug=task_info.get('debug', False),
            parallel=task_info.get('parallel', False),
            task_args=task_info.get('task_args', [])
        )