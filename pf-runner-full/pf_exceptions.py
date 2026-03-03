#!/usr/bin/env python3
"""
pf_exceptions.py - Custom exception classes for the pf runner

This module provides specialized exception classes that capture detailed
context about failures, including:
- Full Python tracebacks
- Environment variables at time of failure
- Execution context (container, subshell, etc.)
- User-friendly error messages with suggestions

The philosophy is to be transparent with users - show them exactly what
went wrong, where it happened, and what the environment looked like.
"""

import os
import sys
import traceback
import platform
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


def _detect_container_environment() -> Optional[str]:
    """
    Detect if we're running inside a container and return container type.
    
    Returns:
        Container type string (e.g., 'docker', 'podman', 'lxc') or None
    """
    # Check for /.dockerenv file (Docker)
    if os.path.exists('/.dockerenv'):
        return 'docker'
    
    # Check /proc/1/cgroup for container indicators
    try:
        with open('/proc/1/cgroup', 'r') as f:
            content = f.read()
            if 'docker' in content:
                return 'docker'
            if 'lxc' in content:
                return 'lxc'
            if 'kubepods' in content:
                return 'kubernetes'
    except (FileNotFoundError, PermissionError):
        pass
    
    # Check for container environment variables
    if os.getenv('container'):
        return os.getenv('container')
    
    return None


def _detect_subshell_depth() -> int:
    """
    Detect how many subshells deep we are.
    
    Returns:
        Number of subshell levels (0 = no subshell)
    """
    # Count SHLVL if available
    shlvl = os.getenv('SHLVL')
    if shlvl and shlvl.isdigit():
        return max(0, int(shlvl) - 1)
    return 0


def _get_platform_info() -> Dict[str, str]:
    """Get platform information for error context."""
    info = {
        'system': platform.system(),
        'machine': platform.machine(),
        'python_version': platform.python_version(),
    }
    
    # Add OS-specific details
    if platform.system() == 'Linux':
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        info['os'] = line.split('=', 1)[1].strip().strip('"')
                        break
        except (FileNotFoundError, PermissionError):
            info['os'] = 'Linux (unknown distribution)'
    elif platform.system() == 'Windows':
        info['os'] = platform.platform()
    elif platform.system() == 'Darwin':
        info['os'] = f"macOS {platform.mac_ver()[0]}"
    
    return info


def _format_environment_context() -> str:
    """
    Format execution environment context for error messages.
    
    Returns:
        Formatted string describing the execution environment
    """
    lines = []
    
    # Container detection
    container = _detect_container_environment()
    if container:
        lines.append(f"  Container: Running in {container} container")
    else:
        lines.append("  Container: Not in a container")
    
    # Subshell depth
    depth = _detect_subshell_depth()
    if depth > 0:
        lines.append(f"  Subshell: {depth} level{'s' if depth > 1 else ''} deep")
    else:
        lines.append("  Subshell: Direct shell (no subshell)")
    
    # Platform info
    platform_info = _get_platform_info()
    lines.append(f"  Platform: {platform_info.get('os', 'Unknown OS')} ({platform_info['machine']})")
    lines.append(f"  Python: {platform_info['python_version']}")
    
    # Current working directory
    lines.append(f"  CWD: {os.getcwd()}")
    
    # User and permissions
    if hasattr(os, 'geteuid'):
        uid = os.geteuid()
        lines.append(f"  User: UID {uid} {'(root)' if uid == 0 else '(non-root)'}")
    
    return "\n".join(lines)


@dataclass
class PFException(Exception):
    """
    Base exception class for all pf-related errors.
    
    This exception captures comprehensive context about the failure:
    - Error message
    - Full traceback
    - Environment variables
    - Execution context (container, subshell, platform)
    - Optional suggestions for fixing the issue
    """
    message: str
    suggestion: Optional[str] = None
    task_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    command: Optional[str] = None
    exit_code: Optional[int] = None
    environment: Dict[str, str] = field(default_factory=dict)
    _traceback: Optional[str] = None
    _context: Optional[str] = None
    
    def __post_init__(self):
        """Capture traceback and context at creation time."""
        # Capture current environment if not provided
        if not self.environment:
            # Capture relevant environment variables
            relevant_vars = [
                'PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'SHLVL',
                'VIRTUAL_ENV', 'CONDA_DEFAULT_ENV', 'NODE_ENV',
                'RUST_BACKTRACE', 'PYTHONPATH', 'LD_LIBRARY_PATH'
            ]
            self.environment = {
                k: v for k, v in os.environ.items() 
                if k in relevant_vars or k.startswith('PF_')
            }
        
        # Capture execution context
        if not self._context:
            self._context = _format_environment_context()
        
        # Capture traceback if not already set
        if not self._traceback:
            self._traceback = ''.join(traceback.format_stack()[:-1])
    
    def format_error(self, include_traceback: bool = True, 
                    include_environment: bool = True) -> str:
        """
        Format the error for display to the user.
        
        Args:
            include_traceback: Include Python traceback in output
            include_environment: Include environment variables in output
            
        Returns:
            Formatted error message
        """
        lines = []
        
        # Header
        lines.append("=" * 70)
        lines.append("PF ERROR")
        lines.append("=" * 70)
        
        # Error location
        if self.task_name:
            lines.append(f"Task: {self.task_name}")
        if self.file_path:
            location = f"File: {self.file_path}"
            if self.line_number:
                location += f", line {self.line_number}"
            lines.append(location)
        if self.command:
            lines.append(f"Command: {self.command}")
        
        # Main error message
        lines.append("")
        lines.append(f"Error: {self.message}")
        
        # Exit code if available
        if self.exit_code is not None:
            lines.append(f"Exit Code: {self.exit_code}")
        
        # Suggestion
        if self.suggestion:
            lines.append("")
            lines.append(f"Suggestion: {self.suggestion}")
        
        # Execution context
        lines.append("")
        lines.append("Execution Context:")
        lines.append(self._context)
        
        # Environment variables
        if include_environment and self.environment:
            lines.append("")
            lines.append("Relevant Environment Variables:")
            for key, value in sorted(self.environment.items()):
                # Truncate long values
                display_value = value if len(value) < 80 else value[:77] + "..."
                lines.append(f"  {key}={display_value}")
        
        # Traceback
        if include_traceback and self._traceback:
            lines.append("")
            lines.append("Python Traceback:")
            lines.append(self._traceback)
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        """String representation shows the formatted error."""
        return self.format_error()


class PFSyntaxError(PFException):
    """
    Exception for syntax errors in PF files.
    
    This is raised when the pf file has invalid syntax, such as:
    - Unclosed blocks (task, if, for)
    - Invalid operators (===, etc.)
    - Missing required keywords
    - Malformed task definitions
    """
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            suggestion=kwargs.pop('suggestion', 
                "Run 'pf prune' to check syntax and get detailed error information"),
            **kwargs
        )


class PFExecutionError(PFException):
    """
    Exception for command execution failures.
    
    This is raised when:
    - A shell command fails (non-zero exit code)
    - A subprocess cannot be started
    - Remote command execution fails
    """
    
    # Maximum file size to check for PE signature (10MB)
    MAX_FILE_SIZE_FOR_PE_CHECK = 10 * 1024 * 1024
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, **kwargs)
        
        # Add PE executable detection if on Linux trying to run Windows binary
        # Only suggest this for specific error codes that indicate execution issues
        if (kwargs.get('exit_code') in (126, 127, -1) and 
            platform.system() == 'Linux' and 
            kwargs.get('command')):
            cmd = kwargs.get('command', '')
            
            # Check if command looks like it might be a Windows binary
            # Look for common Windows executable patterns
            is_likely_pe = False
            
            # Check file extension
            if cmd.endswith('.exe') or cmd.endswith('.dll') or cmd.endswith('.bat'):
                is_likely_pe = True
            
            # Check if the file exists and we can read it to verify
            # Extract the actual executable path from the command
            parts = cmd.split()
            if parts:
                exe_path = parts[0]
                # Validate path is reasonable before attempting to read
                # Only check files that exist and are regular files
                if os.path.exists(exe_path) and os.path.isfile(exe_path):
                    try:
                        # Get absolute path to avoid directory traversal
                        abs_path = os.path.abspath(exe_path)
                        
                        # Additional security: only read if file size is reasonable
                        if os.path.getsize(abs_path) < self.MAX_FILE_SIZE_FOR_PE_CHECK:
                            # Read first few bytes to check for PE signature (MZ header)
                            with open(abs_path, 'rb') as f:
                                magic = f.read(2)
                                if magic == b'MZ':
                                    is_likely_pe = True
                    except (IOError, PermissionError, OSError):
                        # Can't read file, fall back to extension check
                        pass
            
            if is_likely_pe:
                container = _detect_container_environment()
                if container:
                    self.suggestion = (
                        f"You appear to be trying to execute a Windows PE executable "
                        f"inside a {container} container on Linux. "
                        "Consider using Wine or running this in a Windows environment."
                    )
                else:
                    self.suggestion = (
                        f"You appear to be trying to execute a Windows PE executable "
                        f"on Linux. Consider using Wine or running this "
                        "in a Windows environment."
                    )


class PFEnvironmentError(PFException):
    """
    Exception for environment-related issues.
    
    This is raised when:
    - Required environment variables are missing
    - Environment variable expansion fails
    - Path resolution fails in the current environment
    """
    
    def __init__(self, message: str, **kwargs):
        # Enhance the message with environment context
        depth = _detect_subshell_depth()
        if depth > 0:
            message += (
                f"\n\nNote: You are {depth} subshell level{'s' if depth > 1 else ''} deep. "
                "Environment variables may not have propagated correctly."
            )
        
        super().__init__(
            message=message,
            suggestion=kwargs.pop('suggestion', 
                "Check that all required environment variables are set and exported"),
            **kwargs
        )


class PFTaskNotFoundError(PFException):
    """
    Exception for when a requested task doesn't exist.
    
    This is raised when:
    - A task name is not found in the Pfyfile
    - An included file cannot be loaded
    """
    
    def __init__(self, task_name: str, available_tasks: Optional[List[str]] = None, **kwargs):
        message = f"Task '{task_name}' not found"
        
        # Try to suggest similar task names
        suggestion = None
        explicit = kwargs.pop('suggestion', None)
        if available_tasks:
            # Simple fuzzy matching - find tasks with similar prefixes
            similar = [t for t in available_tasks if t.startswith(task_name[:3])]
            if similar:
                suggestion = f"Did you mean one of these? {', '.join(similar[:5])}"
        
        super().__init__(
            message=message,
            task_name=task_name,
            suggestion=explicit or suggestion or "Run 'pf list' to see all available tasks",
            **kwargs
        )


class PFConnectionError(PFException):
    """
    Exception for remote connection failures.
    
    This is raised when:
    - SSH connection fails
    - Remote host is unreachable
    - Authentication fails
    """
    
    def __init__(self, message: str, host: Optional[str] = None, **kwargs):
        if host:
            message = f"Connection failed to {host}: {message}"
        
        super().__init__(
            message=message,
            suggestion=kwargs.pop('suggestion', 
                "Check that the host is reachable and credentials are correct"),
            **kwargs
        )


def format_exception_for_user(exc: Exception, include_traceback: bool = True) -> str:
    """
    Format any exception for user-friendly display.
    
    This function handles both PFException instances and regular Python exceptions,
    ensuring users always get useful error information.
    
    Args:
        exc: The exception to format
        include_traceback: Whether to include the traceback
        
    Returns:
        Formatted error message
    """
    if isinstance(exc, PFException):
        return exc.format_error(include_traceback=include_traceback)
    
    # For non-PF exceptions, create a basic formatted output
    lines = []
    lines.append("=" * 70)
    lines.append("UNEXPECTED ERROR")
    lines.append("=" * 70)
    lines.append(f"Error Type: {type(exc).__name__}")
    lines.append(f"Error: {str(exc)}")
    lines.append("")
    lines.append("Execution Context:")
    lines.append(_format_environment_context())
    
    if include_traceback:
        lines.append("")
        lines.append("Python Traceback:")
        lines.append(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    
    lines.append("=" * 70)
    return "\n".join(lines)


# Export all exception classes
__all__ = [
    'PFException',
    'PFSyntaxError',
    'PFExecutionError',
    'PFEnvironmentError',
    'PFTaskNotFoundError',
    'PFConnectionError',
    'format_exception_for_user',
]
