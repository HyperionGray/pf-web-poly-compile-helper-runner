"""
Lark-based parser for pf DSL.

This module provides a robust, grammar-based parser using Lark,
replacing the simple string-based parsing in pf_parser.py.
"""

from typing import Dict, List, Optional, Any
from lark import Lark, Transformer, Tree, Token
from pathlib import Path


# Get the directory containing this file
PARSER_DIR = Path(__file__).parent
GRAMMAR_FILE = PARSER_DIR / "pf.lark"


class PfTransformer(Transformer):
    """
    Transform the Lark parse tree into pf-runner data structures.
    
    This transformer converts the abstract syntax tree (AST) produced
    by Lark into the Task and Statement objects used by the runner.
    """
    
    def __init__(self):
        super().__init__()
        self.tasks = {}
        self.current_task = None
    
    @staticmethod
    def _strip_quotes(value: str) -> str:
        """Helper to strip quotes from string values."""
        if isinstance(value, str):
            return value.strip('"')
        return value
    
    def start(self, items):
        """Top-level rule: returns all parsed tasks."""
        return self.tasks
    
    def statement(self, items):
        """Process a top-level statement."""
        return items[0] if items else None
    
    def task(self, items):
        """Process a task definition."""
        # items format: [IDENTIFIER, param1, param2, ..., NEWLINE, body_items..., END]
        task_name = str(items[0])
        params = {}
        body_items = []
        
        # Skip the task name and collect params and body
        i = 1
        while i < len(items):
            item = items[i]
            if isinstance(item, Token):
                # Skip NEWLINE and END tokens
                i += 1
                continue
            elif isinstance(item, dict):
                # Check if this is a param or body item
                if 'type' in item:
                    # It's a body item
                    body_items.append(item)
                else:
                    # It's a param
                    params.update(item)
            i += 1
        
        task_data = {
            'name': task_name,
            'params': params,
            'body': body_items,
            'description': None
        }
        
        # Extract description if present
        for item in body_items:
            if isinstance(item, dict) and item.get('type') == 'describe':
                task_data['description'] = item.get('text')
                break
        
        self.tasks[task_name] = task_data
        return task_data
    
    def param(self, items):
        """Process a parameter: name="value"."""
        key = str(items[0])
        value = self._strip_quotes(str(items[1]))
        return {key: value}
    
    def task_body(self, items):
        """Process a task body statement."""
        return items[0] if items else None
    
    def describe(self, items):
        """Process a describe statement."""
        text = str(items[0])
        return {'type': 'describe', 'text': text}
    
    def shell(self, items):
        """Process a shell command."""
        command = str(items[0])
        return {'type': 'shell', 'command': command}
    
    def env_stmt(self, items):
        """Process an env statement."""
        env_line = str(items[0])
        return {'type': 'env', 'line': env_line}
    
    def packages_stmt(self, items):
        """Process a packages statement."""
        action = str(items[0])
        packages = [str(pkg) for pkg in items[1:]]
        return {'type': 'packages', 'action': action, 'packages': packages}
    
    def packages_action(self, items):
        """Process packages action (install/remove)."""
        return str(items[0])
    
    def package_name(self, items):
        """Process package name."""
        return str(items[0])
    
    def service_stmt(self, items):
        """Process a service statement."""
        action = str(items[0])
        service_name = str(items[1])
        return {'type': 'service', 'action': action, 'name': service_name}
    
    def service_action(self, items):
        """Process service action."""
        return str(items[0])
    
    def directory_stmt(self, items):
        """Process a directory statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'directory', 'line': args_line}
    
    def copy_stmt(self, items):
        """Process a copy statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'copy', 'line': args_line}
    
    def makefile_stmt(self, items):
        """Process a makefile/make statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'makefile', 'line': args_line}
    
    def cmake_stmt(self, items):
        """Process a cmake statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'cmake', 'line': args_line}
    
    def meson_stmt(self, items):
        """Process a meson/ninja statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'meson', 'line': args_line}
    
    def cargo_stmt(self, items):
        """Process a cargo statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'cargo', 'line': args_line}
    
    def go_build_stmt(self, items):
        """Process a go_build statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'go_build', 'line': args_line}
    
    def configure_stmt(self, items):
        """Process a configure statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'configure', 'line': args_line}
    
    def justfile_stmt(self, items):
        """Process a justfile/just statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'justfile', 'line': args_line}
    
    def autobuild_stmt(self, items):
        """Process an autobuild statement."""
        args_line = str(items[0]) if items else ""
        return {'type': 'autobuild', 'line': args_line}
    
    def build_detect_stmt(self, items):
        """Process a build_detect statement."""
        return {'type': 'build_detect'}
    
    def sync_stmt(self, items):
        """Process a sync statement."""
        kv_pairs = {}
        for item in items:
            if isinstance(item, dict):
                kv_pairs.update(item)
        return {'type': 'sync', 'args': kv_pairs}
    
    def sync_kv(self, items):
        """Process sync key-value pair."""
        if len(items) == 1:
            # Flag (just identifier)
            return {str(items[0]): True}
        elif len(items) == 2:
            # key=value
            key = str(items[0])
            value = items[1]
            if isinstance(value, str):
                return {key: self._strip_quotes(value)}
            else:
                # Array value
                return {key: value}
        return {}
    
    def if_stmt(self, items):
        """Process an if statement."""
        condition = items[0]
        if_body = items[1] if len(items) > 1 else []
        else_body = items[2] if len(items) > 2 else None
        return {
            'type': 'if',
            'condition': condition,
            'if_body': if_body,
            'else_body': else_body
        }
    
    def if_body(self, items):
        """Process if body."""
        return items
    
    def else_body(self, items):
        """Process else body."""
        return items
    
    def condition(self, items):
        """Process condition."""
        return items[0] if items else None
    
    def var_equals(self, items):
        """Process variable equality check."""
        var = items[0]
        op = str(items[1])
        value = self._strip_quotes(str(items[2]))
        return {'type': 'var_equals', 'var': var, 'op': op, 'value': value}
    
    def var_exists(self, items):
        """Process variable existence check."""
        var = items[0]
        return {'type': 'var_exists', 'var': var}
    
    def command_succeeds(self, items):
        """Process command success check."""
        command = str(items[1])  # Skip backticks
        return {'type': 'command_succeeds', 'command': command}
    
    def for_loop(self, items):
        """Process for loop."""
        var_name = str(items[0])
        iterable = items[1]
        body = items[2:] if len(items) > 2 else []
        return {
            'type': 'for',
            'var': var_name,
            'iterable': iterable,
            'body': body
        }
    
    def iterable(self, items):
        """Process iterable (array or variable)."""
        return items[0] if items else None
    
    def array(self, items):
        """Process array literal."""
        values = [self._strip_quotes(str(item)) for item in items if not isinstance(item, Token)]
        return {'type': 'array', 'values': values}
    
    def variable(self, items):
        """Process variable reference."""
        var_name = str(items[0])
        return {'type': 'variable', 'name': var_name}
    
    def arg(self, items):
        """Process a generic argument."""
        if len(items) == 1:
            # Simple identifier or string
            val = str(items[0])
            return self._strip_quotes(val) if val.startswith('"') else val
        elif len(items) == 2:
            # key=value
            key = str(items[0])
            value = str(items[1])
            return {key: self._strip_quotes(value) if value.startswith('"') else value}
        return None
    
    def comment(self, items):
        """Process a comment (ignored)."""
        return None
    
    def env_var(self, items):
        """Process global env var (ignored for now)."""
        return None
    
    def _process_args(self, items):
        """Helper to process list of arguments."""
        args = []
        kwargs = {}
        for item in items:
            if isinstance(item, dict):
                kwargs.update(item)
            elif isinstance(item, str):
                args.append(item)
        return {'positional': args, 'named': kwargs}


class PfLarkParser:
    """
    Lark-based parser for .pf files.
    
    Provides a robust, grammar-based parsing mechanism with proper
    error handling and AST generation.
    """
    
    def __init__(self, grammar_file: Optional[Path] = None):
        """
        Initialize the parser.
        
        Args:
            grammar_file: Path to the .lark grammar file. If None, uses default.
        """
        if grammar_file is None:
            grammar_file = GRAMMAR_FILE
        
        with open(grammar_file, 'r') as f:
            grammar = f.read()
        
        self.parser = Lark(grammar, parser='lalr', start='start')
        self.transformer = PfTransformer()
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse pf file content into tasks.
        
        Args:
            text: The content of the .pf file
            
        Returns:
            Dictionary mapping task names to task data
            
        Raises:
            ValueError: If parsing fails with details from Lark
        """
        try:
            tree = self.parser.parse(text)
            tasks = self.transformer.transform(tree)
            return tasks
        except Exception as e:
            # Preserve the original exception type and message for debugging
            error_type = type(e).__name__
            raise ValueError(f"Failed to parse pf file ({error_type}): {str(e)}") from e
    
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a .pf file.
        
        Args:
            filepath: Path to the .pf file
            
        Returns:
            Dictionary mapping task names to task data
        """
        with open(filepath, 'r') as f:
            content = f.read()
        return self.parse(content)


# Convenience function for quick parsing
def parse_pf(text: str) -> Dict[str, Any]:
    """
    Parse pf DSL text using Lark grammar.
    
    Args:
        text: The pf DSL text to parse
        
    Returns:
        Dictionary of parsed tasks
    """
    parser = PfLarkParser()
    return parser.parse(text)
