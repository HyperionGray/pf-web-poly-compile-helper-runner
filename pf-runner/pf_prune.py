#!/usr/bin/env python3
"""
pf_prune.py - Syntax checking and pruning for pf DSL files

This module provides:
- Syntax checking with --dry-run / -d option
- pf prune command that validates all tasks
- Writing failed tasks to pfail.fail.pf for correction
- Verbose error messages with stack tracebacks
- Debug mode toggle (pf debug-on / pf debug-off)
"""

import os
import sys
import re
import traceback
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path

# Try to import lark for better parsing
try:
    from lark import Lark, UnexpectedInput, UnexpectedCharacters, UnexpectedToken
    from lark.exceptions import LarkError
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False

# Import from existing pf modules
from pf_parser import (
    _find_pfyfile, _load_pfy_source_with_includes, parse_pfyfile_text
)

# Import custom exceptions
from pf_exceptions import (
    PFSyntaxError as PFSyntaxException,
    format_exception_for_user
)


# Debug mode configuration file location
DEBUG_CONFIG_FILE = os.path.expanduser("~/.pf_debug_mode")
DEBUG_LOCK_FILE = os.path.expanduser("~/.pf_debug_lock")


@dataclass
class SyntaxError:
    """Represents a syntax error in a pf file."""
    line_number: int
    column: int
    line_content: str
    error_message: str
    task_name: Optional[str] = None
    suggestion: Optional[str] = None
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    traceback: Optional[str] = None
    
    def format(self, verbose: bool = False) -> str:
        """Format the error for display."""
        lines = []
        
        # Header
        if self.task_name:
            lines.append(f"Error in task '{self.task_name}' at line {self.line_number}:")
        else:
            lines.append(f"Syntax error at line {self.line_number}, column {self.column}:")
        
        # Context before
        for i, ctx in enumerate(self.context_before):
            ctx_line = self.line_number - len(self.context_before) + i
            lines.append(f"  {ctx_line:4d} | {ctx}")
        
        # Error line with pointer
        lines.append(f"  {self.line_number:4d} | {self.line_content}")
        if self.column > 0:
            pointer = " " * (9 + self.column - 1) + "^"
            lines.append(pointer)
        
        # Context after
        for i, ctx in enumerate(self.context_after):
            ctx_line = self.line_number + i + 1
            lines.append(f"  {ctx_line:4d} | {ctx}")
        
        # Error message
        lines.append(f"\n  {self.error_message}")
        
        # Suggestion
        if self.suggestion:
            lines.append(f"\n  Hint: {self.suggestion}")
        
        # Full traceback in debug/verbose mode
        if verbose and self.traceback:
            lines.append("\n  Stack trace:")
            for tb_line in self.traceback.split("\n"):
                lines.append(f"    {tb_line}")
        
        return "\n".join(lines)


@dataclass
class ValidationResult:
    """Result of validating a pf file or task."""
    is_valid: bool
    errors: List[SyntaxError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    task_name: Optional[str] = None
    source_file: Optional[str] = None
    

class PfSyntaxChecker:
    """Syntax checker for pf DSL files with verbose error reporting."""
    
    # Known DSL verbs and their expected patterns
    KNOWN_VERBS = {
        'shell': {'min_args': 1, 'pattern': r'shell\s+.+'},
        'describe': {'min_args': 1, 'pattern': r'describe\s+.+'},
        'env': {'min_args': 1, 'pattern': r'env\s+\S+.*'},
        'shell_lang': {'min_args': 1, 'pattern': r'shell_lang\s+\w+'},
        'packages': {'min_args': 2, 'pattern': r'packages\s+(install|remove)\s+.+'},
        'service': {'min_args': 2, 'pattern': r'service\s+(start|stop|enable|disable|restart)\s+\S+'},
        'directory': {'min_args': 1, 'pattern': r'directory\s+\S+'},
        'copy': {'min_args': 2, 'pattern': r'copy\s+\S+\s+\S+'},
        'sync': {'min_args': 1, 'pattern': r'sync\s+.+'},
        'if': {'min_args': 1, 'pattern': r'if\s+.+'},
        'for': {'min_args': 3, 'pattern': r'for\s+\w+\s+in\s+.+'},
        'makefile': {'min_args': 0, 'pattern': r'(makefile|make)(\s+.*)?'},
        'cmake': {'min_args': 0, 'pattern': r'cmake(\s+.*)?'},
        'meson': {'min_args': 0, 'pattern': r'(meson|ninja)(\s+.*)?'},
        'cargo': {'min_args': 0, 'pattern': r'cargo(\s+.*)?'},
        'go_build': {'min_args': 0, 'pattern': r'(go_build|gobuild)(\s+.*)?'},
        'configure': {'min_args': 0, 'pattern': r'configure(\s+.*)?'},
        'justfile': {'min_args': 0, 'pattern': r'(justfile|just)(\s+.*)?'},
        'autobuild': {'min_args': 0, 'pattern': r'(autobuild|auto_build)(\s+.*)?'},
        'build_detect': {'min_args': 0, 'pattern': r'(build_detect|detect_build)'},
    }
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode or is_debug_enabled()
        self._lark_parser = None
        
    def _get_lark_parser(self):
        """Get or create the Lark parser for grammar validation."""
        if not LARK_AVAILABLE:
            return None
            
        if self._lark_parser is not None:
            return self._lark_parser
            
        # Try to load the grammar file
        grammar_file = Path(__file__).parent / "pf.lark"
        if grammar_file.exists():
            try:
                with open(grammar_file, 'r') as f:
                    grammar = f.read()
                self._lark_parser = Lark(grammar, parser='lalr', start='start')
            except Exception:
                pass
        return self._lark_parser
    
    def _get_error_suggestion(self, line: str, error_type: str) -> Optional[str]:
        """Get a suggestion for fixing common errors."""
        stripped = line.strip()
        
        # Missing 'end' keyword
        if 'end' in error_type.lower() or 'eof' in error_type.lower():
            return "Make sure all 'task', 'if', and 'for' blocks are closed with 'end'"
        
        # Invalid operator
        if '===' in stripped:
            return "Use '==' instead of '===' for equality comparison"
        if '<=' in stripped or '>=' in stripped or '<' in stripped or '>' in stripped:
            return "pf only supports '==' and '!=' operators for conditionals"
        
        # Missing 'in' keyword in for loop
        if stripped.startswith('for ') and ' in ' not in stripped:
            return "For loops require 'in' keyword: for item in [\"a\", \"b\"]"
        
        # Invalid packages action
        if stripped.startswith('packages '):
            parts = stripped.split()
            if len(parts) >= 2 and parts[1] not in ('install', 'remove'):
                return f"Unknown packages action '{parts[1]}'. Use 'install' or 'remove'"
        
        # Invalid service action
        if stripped.startswith('service '):
            parts = stripped.split()
            valid_actions = ('start', 'stop', 'enable', 'disable', 'restart')
            if len(parts) >= 2 and parts[1] not in valid_actions:
                return f"Unknown service action '{parts[1]}'. Use one of: {', '.join(valid_actions)}"
        
        # Unclosed quote
        if stripped.count('"') % 2 != 0:
            return "Unclosed string literal - missing closing quote"
        
        # Task without name
        if stripped == 'task' or stripped == 'task ':
            return "Task name is required: task my-task-name"
        
        return None
    
    def _get_context_lines(self, lines: List[str], line_num: int, context: int = 2) -> Tuple[List[str], List[str]]:
        """Get context lines before and after the error line."""
        before = []
        after = []
        
        # Lines before (0-indexed)
        for i in range(max(0, line_num - context - 1), line_num - 1):
            if i < len(lines):
                before.append(lines[i].rstrip())
        
        # Lines after
        for i in range(line_num, min(len(lines), line_num + context)):
            after.append(lines[i].rstrip())
        
        return before, after
    
    def validate_syntax(self, source: str, source_file: Optional[str] = None) -> ValidationResult:
        """Validate the syntax of a pf DSL source string."""
        errors = []
        warnings = []
        lines = source.splitlines()
        
        # Track block structure
        block_stack = []  # Stack of (type, line_number, name)
        current_task = None
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Track task blocks
            if stripped.startswith('task '):
                try:
                    parts = stripped[5:].split()
                    task_name = parts[0] if parts else None
                    block_stack.append(('task', i, task_name))
                    current_task = task_name
                except Exception as e:
                    ctx_before, ctx_after = self._get_context_lines(lines, i)
                    errors.append(SyntaxError(
                        line_number=i,
                        column=1,
                        line_content=line.rstrip(),
                        error_message=f"Invalid task definition: {e}",
                        task_name=current_task,
                        suggestion="Task definition format: task task-name [param=\"value\"]",
                        context_before=ctx_before,
                        context_after=ctx_after,
                        traceback=traceback.format_exc() if self.debug_mode else None
                    ))
            
            # Track if blocks
            elif stripped.startswith('if '):
                block_stack.append(('if', i, None))
                # Check for invalid operator
                if '===' in stripped:
                    ctx_before, ctx_after = self._get_context_lines(lines, i)
                    errors.append(SyntaxError(
                        line_number=i,
                        column=stripped.find('===') + 1,
                        line_content=line.rstrip(),
                        error_message="Invalid operator '===', use '==' instead",
                        task_name=current_task,
                        suggestion="pf uses '==' for equality, not '===' (JavaScript style)",
                        context_before=ctx_before,
                        context_after=ctx_after
                    ))
            
            # Track for blocks
            elif stripped.startswith('for '):
                block_stack.append(('for', i, None))
                # Check for 'in' keyword
                if ' in ' not in stripped:
                    ctx_before, ctx_after = self._get_context_lines(lines, i)
                    errors.append(SyntaxError(
                        line_number=i,
                        column=stripped.find('for') + 4,
                        line_content=line.rstrip(),
                        error_message="For loop missing 'in' keyword",
                        task_name=current_task,
                        suggestion="Use: for item in [\"a\", \"b\", \"c\"]",
                        context_before=ctx_before,
                        context_after=ctx_after
                    ))
            
            # Handle end keyword
            elif stripped == 'end':
                if not block_stack:
                    ctx_before, ctx_after = self._get_context_lines(lines, i)
                    errors.append(SyntaxError(
                        line_number=i,
                        column=1,
                        line_content=line.rstrip(),
                        error_message="Unexpected 'end' - no matching block to close",
                        task_name=current_task,
                        context_before=ctx_before,
                        context_after=ctx_after
                    ))
                else:
                    block_type, _, _ = block_stack.pop()
                    if block_type == 'task':
                        current_task = None
            
            # Handle else keyword (part of if block)
            elif stripped == 'else':
                # else should be inside an if block
                if not block_stack or block_stack[-1][0] != 'if':
                    ctx_before, ctx_after = self._get_context_lines(lines, i)
                    errors.append(SyntaxError(
                        line_number=i,
                        column=1,
                        line_content=line.rstrip(),
                        error_message="Unexpected 'else' - not inside an 'if' block",
                        task_name=current_task,
                        suggestion="'else' must be inside an 'if' block",
                        context_before=ctx_before,
                        context_after=ctx_after
                    ))
                # else is valid - don't pop the if block, just continue
            
            # Validate known verbs
            else:
                verb = stripped.split()[0] if stripped else None
                if verb and current_task:  # Inside a task
                    # Check for invalid operators in conditionals
                    if '===' in stripped:
                        ctx_before, ctx_after = self._get_context_lines(lines, i)
                        errors.append(SyntaxError(
                            line_number=i,
                            column=stripped.find('===') + 1,
                            line_content=line.rstrip(),
                            error_message="Invalid operator '===', use '==' instead",
                            task_name=current_task,
                            suggestion="pf uses '==' for equality, not '===' (JavaScript style)",
                            context_before=ctx_before,
                            context_after=ctx_after
                        ))
                    
                    # Check packages action
                    if verb == 'packages':
                        parts = stripped.split()
                        if len(parts) >= 2:
                            action = parts[1]
                            if action not in ('install', 'remove'):
                                ctx_before, ctx_after = self._get_context_lines(lines, i)
                                errors.append(SyntaxError(
                                    line_number=i,
                                    column=stripped.find(action) + 1,
                                    line_content=line.rstrip(),
                                    error_message=f"Invalid packages action '{action}'",
                                    task_name=current_task,
                                    suggestion="Use 'install' or 'remove': packages install pkg1 pkg2",
                                    context_before=ctx_before,
                                    context_after=ctx_after
                                ))
                    
                    # Check service action
                    if verb == 'service':
                        parts = stripped.split()
                        valid_actions = ('start', 'stop', 'enable', 'disable', 'restart')
                        if len(parts) >= 2:
                            action = parts[1]
                            if action not in valid_actions:
                                ctx_before, ctx_after = self._get_context_lines(lines, i)
                                errors.append(SyntaxError(
                                    line_number=i,
                                    column=stripped.find(action) + 1,
                                    line_content=line.rstrip(),
                                    error_message=f"Invalid service action '{action}'",
                                    task_name=current_task,
                                    suggestion=f"Valid actions: {', '.join(valid_actions)}",
                                    context_before=ctx_before,
                                    context_after=ctx_after
                                ))
        
        # Check for unclosed blocks
        while block_stack:
            block_type, line_num, name = block_stack.pop()
            ctx_before, ctx_after = self._get_context_lines(lines, line_num)
            name_part = f" '{name}'" if name else ""
            errors.append(SyntaxError(
                line_number=line_num,
                column=1,
                line_content=lines[line_num - 1].rstrip() if line_num <= len(lines) else "",
                error_message=f"Unclosed '{block_type}' block{name_part} - missing 'end'",
                task_name=name if block_type == 'task' else None,
                suggestion=f"Add 'end' to close the {block_type} block",
                context_before=ctx_before,
                context_after=ctx_after
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            source_file=source_file
        )
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a pf file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            return self.validate_syntax(source, source_file=file_path)
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                errors=[SyntaxError(
                    line_number=0,
                    column=0,
                    line_content="",
                    error_message=f"File not found: {file_path}"
                )],
                source_file=file_path
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[SyntaxError(
                    line_number=0,
                    column=0,
                    line_content="",
                    error_message=f"Error reading file: {e}",
                    traceback=traceback.format_exc() if self.debug_mode else None
                )],
                source_file=file_path
            )


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return os.path.exists(DEBUG_CONFIG_FILE)


def set_debug_mode(enabled: bool) -> None:
    """
    Set the debug mode state.
    
    The debug lock is a simple file-based mechanism to prevent accidental changes
    to debug mode during CI/CD pipelines or automated testing. It's not intended
    to be a security mechanism - users can remove the lock file manually if needed.
    """
    # Check if debug mode is locked (e.g., during CI/CD runs)
    if os.path.exists(DEBUG_LOCK_FILE):
        raise PermissionError(
            "Debug mode is locked! Cannot change debug mode while lock is active.\n"
            "If you believe this is an error, remove the lock file at:\n"
            f"  {DEBUG_LOCK_FILE}"
        )
    
    if enabled:
        Path(DEBUG_CONFIG_FILE).touch()
        print("Debug mode enabled")
    else:
        if os.path.exists(DEBUG_CONFIG_FILE):
            os.remove(DEBUG_CONFIG_FILE)
        print("Debug mode disabled")


def lock_debug_mode() -> None:
    """Lock debug mode to prevent changes."""
    Path(DEBUG_LOCK_FILE).touch()
    print(f"Debug mode locked. Remove {DEBUG_LOCK_FILE} to unlock.")


def prune_tasks(
    file_arg: Optional[str] = None,
    dry_run: bool = True,
    verbose: bool = False,
    output_file: str = "pfail.fail.pf"
) -> Tuple[int, int, List[str]]:
    """
    Check syntax of all tasks and collect failures.
    
    Args:
        file_arg: Path to the pf file to check
        dry_run: If True, only check syntax without executing
        verbose: If True, include full stack traces
        output_file: File to write failed tasks to
        
    Returns:
        Tuple of (passed_count, failed_count, failed_task_names)
    """
    debug_mode = is_debug_enabled()
    checker = PfSyntaxChecker(debug_mode=debug_mode or verbose)
    
    # Load the source with includes
    try:
        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=file_arg)
    except Exception as e:
        print(f"Error loading pf file: {e}", file=sys.stderr)
        if debug_mode or verbose:
            traceback.print_exc()
        return 0, 1, []
    
    # Validate the entire source first
    result = checker.validate_syntax(dsl_src, source_file=file_arg)
    
    if not result.is_valid:
        print(f"\n{'='*60}")
        print("Syntax Errors Found")
        print('='*60)
        for error in result.errors:
            print(f"\n{error.format(verbose=debug_mode or verbose)}")
        
        # Collect failed task names from errors
        failed_task_names = set()
        for error in result.errors:
            if error.task_name:
                failed_task_names.add(error.task_name)
        
        # Write failed content to output file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# pf prune - Failed syntax validation\n")
                f.write("# Fix the errors below and re-run pf prune\n\n")
                for error in result.errors:
                    f.write(f"# Error at line {error.line_number}: {error.error_message}\n")
                    if error.suggestion:
                        f.write(f"# Hint: {error.suggestion}\n")
                    f.write(f"# {error.line_content}\n\n")
            print(f"\nFailed tasks written to: {output_file}")
        except Exception as e:
            print(f"Warning: Could not write to {output_file}: {e}", file=sys.stderr)
        
        return 0, len(result.errors), list(failed_task_names)
    
    # File is syntactically valid - count tasks
    tasks = parse_pfyfile_text(dsl_src, task_sources)
    passed = list(tasks.keys())
    
    if verbose:
        for task_name in passed:
            print(f"  ✓ {task_name}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Prune Results")
    print('='*60)
    print(f"  Passed: {len(passed)}")
    print(f"  Failed: 0")
    print("\n✓ All tasks passed syntax validation!")
    
    return len(passed), 0, []


def main(argv: List[str]) -> int:
    """Main entry point for pf prune."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog='pf prune',
        description='Check pf file syntax and report errors'
    )
    parser.add_argument(
        '-f', '--file',
        help='Pfyfile to check (default: Pfyfile.pf)'
    )
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Only check syntax, do not execute (default behavior)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output with stack traces'
    )
    parser.add_argument(
        '-o', '--output',
        default='pfail.fail.pf',
        help='Output file for failed tasks (default: pfail.fail.pf)'
    )
    
    args = parser.parse_args(argv)
    
    # dry_run is always true for prune command - it never executes tasks
    passed, failed, failed_tasks = prune_tasks(
        file_arg=args.file,
        dry_run=True,  # prune always runs in dry-run mode
        verbose=args.verbose,
        output_file=args.output
    )
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
