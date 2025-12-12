#!/usr/bin/env python3
"""
pf_shell.py - Enhanced shell command handling for pf

This module provides:
- Proper parsing of ENV_VAR=value command syntax
- Environment variable handling
- Command execution with proper quoting
- Transparent error reporting with context
"""

import os
import sys
import shlex
import re
import subprocess
from typing import List, Dict, Tuple, Optional

# Import custom exceptions
from pf_exceptions import (
    PFExecutionError,
    PFEnvironmentError,
    format_exception_for_user
)


def parse_shell_command(cmd_line: str) -> Tuple[Dict[str, str], str]:
    """
    Parse shell command line to extract environment variables and command.
    
    Handles syntax like: ENV_VAR=value ENV2=value2 bash -lc "script.sh"
    
    Returns:
        Tuple of (env_vars_dict, remaining_command)
        
    Raises:
        PFExecutionError: If command parsing fails
    """
    env_vars = {}
    
    # Use shlex to properly handle quoted strings
    try:
        tokens = shlex.split(cmd_line)
    except ValueError as e:
        # If shlex fails, raise a detailed error
        raise PFExecutionError(
            message=f"Failed to parse shell command: {e}",
            command=cmd_line,
            suggestion="Check for unclosed quotes or invalid escape sequences"
        )
    
    # Find environment variable assignments at the start
    remaining_tokens = []
    for i, token in enumerate(tokens):
        if '=' in token and not token.startswith('-'):
            # Check if this looks like an environment variable assignment
            key, value = token.split('=', 1)
            # Environment variable names should be valid identifiers
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                env_vars[key] = value
                continue
        
        # Not an env var assignment, rest is the command
        remaining_tokens = tokens[i:]
        break
    
    # Reconstruct the command from remaining tokens
    if remaining_tokens:
        # Try to preserve original quoting where possible
        remaining_cmd = ' '.join(shlex.quote(token) for token in remaining_tokens)
    else:
        remaining_cmd = ''
    
    return env_vars, remaining_cmd


def build_shell_command(env_vars: Dict[str, str], command: str, 
                       task_env: Optional[Dict[str, str]] = None,
                       sudo: bool = False, sudo_user: Optional[str] = None) -> str:
    """
    Build a shell command with proper environment variable handling.
    
    Args:
        env_vars: Environment variables from command line parsing
        command: The actual command to run
        task_env: Additional environment variables from task context
        sudo: Whether to run with sudo
        sudo_user: Specific sudo user
        
    Returns:
        Complete shell command string
    """
    all_env = {}
    if task_env:
        all_env.update(task_env)
    all_env.update(env_vars)
    
    # Build environment variable exports
    env_exports = []
    for key, value in all_env.items():
        env_exports.append(f"export {key}={shlex.quote(str(value))}")
    
    # Combine exports with command
    if env_exports:
        full_command = '; '.join(env_exports) + '; ' + command
    else:
        full_command = command
    
    # Handle sudo if needed
    if sudo:
        if sudo_user:
            full_command = f"sudo -u {shlex.quote(sudo_user)} -H bash -lc {shlex.quote(full_command)}"
        else:
            full_command = f"sudo bash -lc {shlex.quote(full_command)}"
    
    return full_command


def execute_shell_command(cmd_line: str, task_env: Optional[Dict[str, str]] = None,
                         sudo: bool = False, sudo_user: Optional[str] = None,
                         connection=None, prefix: str = "") -> int:
    """
    Execute a shell command with proper environment variable handling.
    
    Args:
        cmd_line: Raw command line (may include ENV_VAR=value syntax)
        task_env: Task-level environment variables
        sudo: Whether to run with sudo
        sudo_user: Specific sudo user
        connection: Fabric connection (None for local)
        prefix: Output prefix for logging
        
    Returns:
        Exit code
    """
    # Parse environment variables from command line
    env_vars, command = parse_shell_command(cmd_line)
    
    if not command:
        print(f"{prefix}[warn] Empty command after parsing environment variables")
        return 0
    
    # Build the complete command
    full_command = build_shell_command(env_vars, command, task_env, sudo, sudo_user)
    
    # Display what we're running
    display_env = {}
    if task_env:
        display_env.update(task_env)
    display_env.update(env_vars)
    
    if display_env:
        env_display = ' '.join([f"{k}={shlex.quote(str(v))}" for k, v in display_env.items()])
        display_cmd = f"{env_display} {command}"
    else:
        display_cmd = command
        
    if sudo:
        display_cmd = f"(sudo) {display_cmd}"
    
    print(f"{prefix}$ {display_cmd}")
    
    # Execute the command
    if connection is None:
        # Local execution
        
        # Build environment for subprocess
        proc_env = dict(os.environ)
        if task_env:
            proc_env.update({k: str(v) for k, v in task_env.items()})
        proc_env.update({k: str(v) for k, v in env_vars.items()})
        
        # For local execution, we can pass env directly to subprocess
        try:
            if sudo:
                # For sudo, we need to use the shell command we built
                p = subprocess.Popen(full_command, shell=True, env=proc_env)
            else:
                # For non-sudo, we can run the command directly with the environment
                p = subprocess.Popen(command, shell=True, env=proc_env)
            
            exit_code = p.wait()
            return exit_code
            
        except subprocess.SubprocessError as e:
            raise PFExecutionError(
                message=f"Failed to execute subprocess: {e}",
                command=display_cmd,
                environment=display_env,
                suggestion="Check that the command exists and is executable"
            )
    else:
        # Remote execution via Fabric
        try:
            result = connection.run(full_command, pty=True, warn=True, hide=False)
            exit_code = result.exited
            return exit_code
            
        except Exception as e:
            raise PFExecutionError(
                message=f"Remote command execution failed: {e}",
                command=display_cmd,
                environment=display_env,
                suggestion="Check network connectivity and remote host accessibility"
            )


def validate_shell_syntax(cmd_line: str) -> Tuple[bool, Optional[str]]:
    """
    Validate shell command syntax.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        env_vars, command = parse_shell_command(cmd_line)
        
        if not command.strip():
            return False, "Empty command after environment variable parsing"
        
        # Basic validation of environment variable names
        for key in env_vars:
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
                return False, f"Invalid environment variable name: {key}"
        
        return True, None
        
    except PFExecutionError as e:
        return False, str(e.message) if hasattr(e, 'message') else str(e)
    except Exception as e:
        return False, f"Shell syntax error: {e}"


# Example usage and tests
if __name__ == "__main__":
    # Test cases
    test_commands = [
        "echo hello",
        "ENV_VAR=value echo hello",
        "PATH=/usr/bin:$PATH NODE_ENV=production npm start",
        'DEBUG=1 bash -lc "echo $DEBUG"',
        "USER=test PORT=3000 node server.js",
    ]
    
    for cmd in test_commands:
        print(f"\nTesting: {cmd}")
        env_vars, remaining = parse_shell_command(cmd)
        print(f"  Env vars: {env_vars}")
        print(f"  Command: {remaining}")
        
        is_valid, error = validate_shell_syntax(cmd)
        print(f"  Valid: {is_valid}")
        if error:
            print(f"  Error: {error}")