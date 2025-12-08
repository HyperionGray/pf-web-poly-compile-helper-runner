#!/usr/bin/env python3
"""
pf_exceptions.py - Custom exception classes for PF with environment context

This module provides:
- PFException base class with environment context capture
- PFSyntaxError for DSL parsing issues
- Environment context collection and reporting
- Container detection and subshell state tracking
"""

import os
import sys
import traceback
import subprocess
import platform
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


class EnvironmentContext:
    """Captures and provides environment context for error reporting."""
    
    def __init__(self):
        self.container_info = self._detect_container()
        self.subshell_level = self._get_subshell_level()
        self.environment_vars = dict(os.environ)
        self.working_directory = os.getcwd()
        self.platform_info = self._get_platform_info()
        self.shell_info = self._get_shell_info()
        
    def _detect_container(self) -> Dict[str, Any]:
        """Detect if running in a container and what type."""
        container_info = {
            'in_container': False,
            'type': None,
            'details': {}
        }
        
        # Check for Docker
        if os.path.exists('/.dockerenv'):
            container_info['in_container'] = True
            container_info['type'] = 'docker'
            
        # Check for Podman
        elif os.path.exists('/run/.containerenv'):
            container_info['in_container'] = True
            container_info['type'] = 'podman'
            try:
                with open('/run/.containerenv', 'r') as f:
                    container_info['details']['containerenv'] = f.read().strip()
            except:
                pass
                
        # Check for LXC/LXD
        elif os.path.exists('/proc/1/environ'):
            try:
                with open('/proc/1/environ', 'rb') as f:
                    environ = f.read().decode('utf-8', errors='ignore')
                    if 'container=lxc' in environ:
                        container_info['in_container'] = True
                        container_info['type'] = 'lxc'
            except:
                pass
                
        # Check for systemd-nspawn
        if not container_info['in_container']:
            try:
                result = subprocess.run(['systemd-detect-virt', '-c'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    container_info['in_container'] = True
                    container_info['type'] = result.stdout.strip()
            except:
                pass
                
        return container_info
        
    def _get_subshell_level(self) -> int:
        """Get the current subshell nesting level."""
        return int(os.environ.get('SHLVL', '1'))
        
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'python_version': platform.python_version()
        }
        
    def _get_shell_info(self) -> Dict[str, Optional[str]]:
        """Get shell information."""
        return {
            'shell': os.environ.get('SHELL'),
            'term': os.environ.get('TERM'),
            'user': os.environ.get('USER'),
            'home': os.environ.get('HOME')
        }
        
    def format_context(self, include_env: bool = False) -> str:
        """Format environment context for error reporting."""
        lines = []
        
        # Container information
        if self.container_info['in_container']:
            lines.append(f"Container: {self.container_info['type']}")
            if self.container_info['details']:
                for key, value in self.container_info['details'].items():
                    lines.append(f"  {key}: {value}")
        else:
            lines.append("Container: Not in container")
            
        # Subshell level
        if self.subshell_level > 1:
            lines.append(f"Subshell level: {self.subshell_level} (nested)")
        else:
            lines.append("Subshell level: 1 (main shell)")
            
        # Platform info
        lines.append(f"Platform: {self.platform_info['system']} {self.platform_info['release']} ({self.platform_info['machine']})")
        lines.append(f"Python: {self.platform_info['python_version']}")
        
        # Shell info
        if self.shell_info['shell']:
            lines.append(f"Shell: {self.shell_info['shell']}")
        if self.shell_info['user']:
            lines.append(f"User: {self.shell_info['user']}")
            
        # Working directory
        lines.append(f"Working directory: {self.working_directory}")
        
        # Environment variables (if requested)
        if include_env:
            lines.append("\nEnvironment variables:")
            for key, value in sorted(self.environment_vars.items()):
                # Mask sensitive variables
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                    value = '***MASKED***'
                lines.append(f"  {key}={value}")
                
        return "\n".join(lines)


class PFException(Exception):
    """Base exception class for PF with environment context."""
    
    def __init__(self, message: str, context: Optional[EnvironmentContext] = None, 
                 cause: Optional[Exception] = None, line_number: Optional[int] = None,
                 file_path: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.context = context or EnvironmentContext()
        self.cause = cause
        self.line_number = line_number
        self.file_path = file_path
        self.traceback_info = traceback.format_exc() if cause else None
        
    def format_error(self, show_traceback: bool = True, show_env: bool = False) -> str:
        """Format the error with context information."""
        lines = []
        
        # Error header
        lines.append(f"PF Error: {self.message}")
        
        # File and line information
        if self.file_path:
            lines.append(f"File: {self.file_path}")
        if self.line_number:
            lines.append(f"Line: {self.line_number}")
            
        # Environment context
        lines.append("\nEnvironment Context:")
        lines.append(self.context.format_context(include_env=show_env))
        
        # Original cause
        if self.cause:
            lines.append(f"\nOriginal error: {type(self.cause).__name__}: {self.cause}")
            
        # Traceback
        if show_traceback and self.traceback_info and self.traceback_info != "NoneType: None\n":
            lines.append("\nFull traceback:")
            lines.append(self.traceback_info)
            
        return "\n".join(lines)
        
    def __str__(self) -> str:
        return self.format_error(show_traceback=False, show_env=False)


class PFSyntaxError(PFException):
    """Exception for PF DSL syntax errors."""
    
    def __init__(self, message: str, line_content: Optional[str] = None, 
                 suggestions: Optional[List[str]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.line_content = line_content
        self.suggestions = suggestions or []
        
    def format_error(self, show_traceback: bool = False, show_env: bool = False) -> str:
        """Format syntax error with additional context."""
        lines = []
        
        # Error header
        lines.append(f"PF Syntax Error: {self.message}")
        
        # File and line information
        if self.file_path:
            lines.append(f"File: {self.file_path}")
        if self.line_number:
            lines.append(f"Line: {self.line_number}")
            
        # Show the problematic line
        if self.line_content:
            lines.append(f"Content: {self.line_content.strip()}")
            
        # Suggestions
        if self.suggestions:
            lines.append("\nSuggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")
                
        # Environment context (usually less relevant for syntax errors)
        if show_env:
            lines.append("\nEnvironment Context:")
            lines.append(self.context.format_context(include_env=show_env))
            
        return "\n".join(lines)


class PFExecutionError(PFException):
    """Exception for command execution errors."""
    
    def __init__(self, message: str, command: Optional[str] = None, 
                 exit_code: Optional[int] = None, stdout: Optional[str] = None,
                 stderr: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        
    def format_error(self, show_traceback: bool = True, show_env: bool = True) -> str:
        """Format execution error with command details."""
        lines = []
        
        # Error header
        lines.append(f"PF Execution Error: {self.message}")
        
        # Command information
        if self.command:
            lines.append(f"Command: {self.command}")
        if self.exit_code is not None:
            lines.append(f"Exit code: {self.exit_code}")
            
        # Output information
        if self.stdout:
            lines.append(f"Stdout: {self.stdout}")
        if self.stderr:
            lines.append(f"Stderr: {self.stderr}")
            
        # Environment context
        lines.append("\nEnvironment Context:")
        lines.append(self.context.format_context(include_env=show_env))
        
        # Original cause and traceback
        if self.cause:
            lines.append(f"\nOriginal error: {type(self.cause).__name__}: {self.cause}")
            
        if show_traceback and self.traceback_info and self.traceback_info != "NoneType: None\n":
            lines.append("\nFull traceback:")
            lines.append(self.traceback_info)
            
        return "\n".join(lines)


class PFEnvironmentError(PFException):
    """Exception for environment-related errors."""
    
    def __init__(self, message: str, env_var: Optional[str] = None, 
                 expected_value: Optional[str] = None, actual_value: Optional[str] = None,
                 **kwargs):
        super().__init__(message, **kwargs)
        self.env_var = env_var
        self.expected_value = expected_value
        self.actual_value = actual_value
        
    def format_error(self, show_traceback: bool = True, show_env: bool = True) -> str:
        """Format environment error with variable details."""
        lines = []
        
        # Error header
        lines.append(f"PF Environment Error: {self.message}")
        
        # Variable information
        if self.env_var:
            lines.append(f"Variable: {self.env_var}")
        if self.expected_value is not None:
            lines.append(f"Expected: {self.expected_value}")
        if self.actual_value is not None:
            lines.append(f"Actual: {self.actual_value}")
            
        # Environment context
        lines.append("\nEnvironment Context:")
        lines.append(self.context.format_context(include_env=show_env))
        
        # Original cause and traceback
        if self.cause:
            lines.append(f"\nOriginal error: {type(self.cause).__name__}: {self.cause}")
            
        if show_traceback and self.traceback_info and self.traceback_info != "NoneType: None\n":
            lines.append("\nFull traceback:")
            lines.append(self.traceback_info)
            
        return "\n".join(lines)


def format_pf_error(exc: Exception, show_traceback: bool = True, show_env: bool = False) -> str:
    """Format any exception as a PF error with context."""
    if isinstance(exc, PFException):
        return exc.format_error(show_traceback=show_traceback, show_env=show_env)
    else:
        # Wrap regular exceptions in PFException for consistent formatting
        context = EnvironmentContext()
        pf_exc = PFException(str(exc), context=context, cause=exc)
        return pf_exc.format_error(show_traceback=show_traceback, show_env=show_env)


def handle_pf_error(exc: Exception, exit_on_error: bool = True, 
                   show_traceback: bool = None, show_env: bool = None) -> int:
    """Handle PF errors with appropriate formatting and exit behavior."""
    
    # Determine default values based on exception type
    if show_traceback is None:
        show_traceback = not isinstance(exc, PFSyntaxError)
    if show_env is None:
        show_env = isinstance(exc, (PFExecutionError, PFEnvironmentError))
        
    # Format and display the error
    error_msg = format_pf_error(exc, show_traceback=show_traceback, show_env=show_env)
    print(error_msg, file=sys.stderr)
    
    # Return appropriate exit code
    exit_code = 1
    if isinstance(exc, PFSyntaxError):
        exit_code = 2
    elif isinstance(exc, PFEnvironmentError):
        exit_code = 3
    elif isinstance(exc, PFExecutionError) and exc.exit_code:
        exit_code = exc.exit_code
        
    if exit_on_error:
        sys.exit(exit_code)
        
    return exit_code