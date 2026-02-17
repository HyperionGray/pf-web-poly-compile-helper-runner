#!/usr/bin/env python3
"""
LLDB Integration for Advanced Kernel Debugging

Provides sophisticated breakpoint management, conditional debugging,
and automated analysis workflows for kernel-mode debugging.
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
import argparse

@dataclass
class Breakpoint:
    """Breakpoint configuration"""
    address: str
    condition: Optional[str] = None
    commands: List[str] = None
    hit_count: int = 0
    enabled: bool = True
    name: Optional[str] = None
    
    def __post_init__(self):
        if self.commands is None:
            self.commands = []

@dataclass
class DebugSession:
    """Debug session configuration"""
    target: str
    breakpoints: List[Breakpoint] = None
    scripts: List[str] = None
    output_file: Optional[str] = None
    
    def __post_init__(self):
        if self.breakpoints is None:
            self.breakpoints = []
        if self.scripts is None:
            self.scripts = []

class LLDBIntegration:
    """Advanced LLDB integration for kernel debugging"""
    
    def __init__(self):
        self.lldb_available = self._check_lldb()
        self.session_scripts = []
        self.vulnerability_patterns = self._load_vuln_patterns()
    
    def _check_lldb(self) -> bool:
        """Check if LLDB is available"""
        try:
            result = subprocess.run(['lldb', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _load_vuln_patterns(self) -> Dict[str, Dict]:
        """Load vulnerability detection patterns for automatic breakpoints"""
        return {
            'buffer_overflow': {
                'functions': ['strcpy', 'sprintf', 'gets', 'strcat'],
                'description': 'Buffer overflow vulnerable functions',
                'commands': [
                    'register read',
                    'memory read $rdi 64',
                    'memory read $rsi 64',
                    'bt'
                ]
            },
            'use_after_free': {
                'functions': ['free', 'kfree', 'vfree'],
                'description': 'Memory deallocation functions',
                'commands': [
                    'register read',
                    'memory read $rdi 32',
                    'bt',
                    'watchpoint set variable $rdi'
                ]
            },
            'privilege_escalation': {
                'functions': ['capable', 'ns_capable', 'security_capable'],
                'description': 'Privilege checking functions',
                'commands': [
                    'register read',
                    'print (int)$rdi',
                    'print (int)$rsi',
                    'bt'
                ]
            },
            'ioctl_handlers': {
                'patterns': ['ioctl', 'unlocked_ioctl', 'compat_ioctl'],
                'description': 'IOCTL handler functions',
                'commands': [
                    'register read',
                    'print (unsigned int)$rsi',
                    'print (unsigned long)$rdx',
                    'memory read $rdx 64',
                    'bt'
                ]
            }
        }
    
    def create_session(self, target: str) -> DebugSession:
        """Create a new debug session"""
        return DebugSession(target=target)
    
    def add_breakpoint(self, session: DebugSession, address: str, 
                      condition: str = None, commands: List[str] = None,
                      name: str = None) -> Breakpoint:
        """Add a breakpoint to the session"""
        bp = Breakpoint(
            address=address,
            condition=condition,
            commands=commands or [],
            name=name
        )
        session.breakpoints.append(bp)
        return bp
    
    def add_vulnerability_breakpoints(self, session: DebugSession, 
                                    vuln_types: List[str] = None) -> List[Breakpoint]:
        """Add automatic breakpoints for vulnerability detection"""
        if vuln_types is None:
            vuln_types = list(self.vulnerability_patterns.keys())
        
        breakpoints = []
        
        for vuln_type in vuln_types:
            if vuln_type not in self.vulnerability_patterns:
                continue
            
            pattern = self.vulnerability_patterns[vuln_type]
            
            # Add breakpoints for functions
            if 'functions' in pattern:
                for func in pattern['functions']:
                    bp = self.add_breakpoint(
                        session,
                        address=func,
                        commands=pattern.get('commands', []),
                        name=f"{vuln_type}_{func}"
                    )
                    breakpoints.append(bp)
        
        return breakpoints
    
    def add_ioctl_analysis_breakpoints(self, session: DebugSession) -> List[Breakpoint]:
        """Add specialized breakpoints for IOCTL analysis"""
        breakpoints = []
        
        # Common IOCTL entry points
        ioctl_functions = [
            'do_vfs_ioctl',
            'vfs_ioctl',
            'sys_ioctl',
            'compat_sys_ioctl'
        ]
        
        for func in ioctl_functions:
            commands = [
                'register read',
                'print (int)$rdi',  # fd
                'print (unsigned int)$rsi',  # cmd
                'print (unsigned long)$rdx',  # arg
                'memory read $rdx 64',
                'bt 10'
            ]
            
            bp = self.add_breakpoint(
                session,
                address=func,
                commands=commands,
                name=f"ioctl_{func}"
            )
            breakpoints.append(bp)
        
        return breakpoints
    
    def generate_lldb_script(self, session: DebugSession) -> str:
        """Generate LLDB script for the session"""
        script_lines = [
            f"# LLDB Debug Script for {session.target}",
            f"target create {session.target}",
            "",
            "# Set up breakpoints"
        ]
        
        for i, bp in enumerate(session.breakpoints):
            if bp.name:
                script_lines.append(f"# Breakpoint: {bp.name}")
            
            # Set breakpoint
            if bp.address.startswith('0x'):
                script_lines.append(f"breakpoint set --address {bp.address}")
            else:
                script_lines.append(f"breakpoint set --name {bp.address}")
            
            # Add condition if specified
            if bp.condition:
                script_lines.append(f"breakpoint modify --condition '{bp.condition}' {i+1}")
            
            # Add commands if specified
            if bp.commands:
                script_lines.append(f"breakpoint command add {i+1}")
                for cmd in bp.commands:
                    script_lines.append(f"  {cmd}")
                script_lines.append("DONE")
            
            script_lines.append("")
        
        # Add session scripts
        if session.scripts:
            script_lines.extend(["# Custom scripts"] + session.scripts)
        
        # Add run command
        script_lines.extend([
            "",
            "# Start debugging",
            "run",
            "continue"
        ])
        
        return "\n".join(script_lines)
    
    def run_debug_session(self, session: DebugSession, 
                         interactive: bool = False) -> Dict:
        """Run the debug session"""
        if not self.lldb_available:
            raise RuntimeError("LLDB not available")
        
        # Generate script
        script_content = self.generate_lldb_script(session)
        
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
            f.write(script_content)
            script_file = f.name
        
        try:
            if interactive:
                # Run interactive session
                cmd = ['lldb', '-s', script_file]
                subprocess.run(cmd)
                return {'status': 'interactive_session_completed'}
            else:
                # Run batch session
                cmd = ['lldb', '-b', '-s', script_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                return {
                    'status': 'completed',
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'script_file': script_file
                }
        
        finally:
            if not interactive:
                os.unlink(script_file)
    
    def analyze_crash_dump(self, core_file: str, executable: str = None) -> Dict:
        """Analyze a crash dump with LLDB"""
        if not self.lldb_available:
            raise RuntimeError("LLDB not available")
        
        commands = [
            "bt all",
            "register read",
            "thread list",
            "image list",
        ]
        
        if executable:
            cmd_line = f"lldb -c {core_file} {executable}"
        else:
            cmd_line = f"lldb -c {core_file}"
        
        script_content = "\n".join(commands + ["quit"])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
            f.write(script_content)
            script_file = f.name
        
        try:
            cmd = cmd_line.split() + ['-s', script_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                'analysis': self._parse_crash_analysis(result.stdout),
                'raw_output': result.stdout,
                'stderr': result.stderr
            }
        
        finally:
            os.unlink(script_file)
    
    def _parse_crash_analysis(self, output: str) -> Dict:
        """Parse crash analysis output"""
        analysis = {
            'crash_type': 'unknown',
            'crash_address': None,
            'stack_trace': [],
            'registers': {},
            'threads': []
        }
        
        lines = output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'frame #' in line:
                analysis['stack_trace'].append(line)
            elif line.startswith('rax =') or line.startswith('eax ='):
                # Parse register values
                parts = line.split()
                for i in range(0, len(parts), 3):
                    if i + 2 < len(parts):
                        reg_name = parts[i]
                        reg_value = parts[i + 2]
                        analysis['registers'][reg_name] = reg_value
        
        return analysis
    
    def create_fuzzing_breakpoints(self, session: DebugSession, 
                                 target_functions: List[str]) -> List[Breakpoint]:
        """Create breakpoints optimized for fuzzing"""
        breakpoints = []
        
        for func in target_functions:
            # Add entry breakpoint
            entry_commands = [
                'register read rdi rsi rdx',
                'memory read $rdi 32',
                'continue'
            ]
            
            bp = self.add_breakpoint(
                session,
                address=func,
                commands=entry_commands,
                name=f"fuzz_entry_{func}"
            )
            breakpoints.append(bp)
        
        # Add crash detection breakpoints
        crash_functions = ['panic', 'BUG', 'oops_begin']
        for func in crash_functions:
            crash_commands = [
                'bt',
                'register read',
                'thread list',
                'quit'
            ]
            
            bp = self.add_breakpoint(
                session,
                address=func,
                commands=crash_commands,
                name=f"crash_{func}"
            )
            breakpoints.append(bp)
        
        return breakpoints

def main():
    parser = argparse.ArgumentParser(description='LLDB Integration for Kernel Debugging')
    parser.add_argument('target', nargs='?', help='Target executable or core dump')
    parser.add_argument('--core', help='Core dump file for analysis')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run interactive debugging session')
    parser.add_argument('--vuln-breakpoints', nargs='*',
                       help='Add vulnerability detection breakpoints')
    parser.add_argument('--ioctl-analysis', action='store_true',
                       help='Add IOCTL analysis breakpoints')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--script', help='Additional LLDB script file')
    
    args = parser.parse_args()
    
    lldb = LLDBIntegration()
    
    if not lldb.lldb_available:
        print("Error: LLDB not available")
        sys.exit(1)
    
    if args.core:
        # Analyze crash dump
        analysis = lldb.analyze_crash_dump(args.core, args.target)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2)
        else:
            print(json.dumps(analysis, indent=2))
    
    elif args.target:
        # Create debug session
        session = lldb.create_session(args.target)
        
        # Add vulnerability breakpoints if requested
        if args.vuln_breakpoints is not None:
            vuln_types = args.vuln_breakpoints if args.vuln_breakpoints else None
            lldb.add_vulnerability_breakpoints(session, vuln_types)
        
        # Add IOCTL analysis breakpoints if requested
        if args.ioctl_analysis:
            lldb.add_ioctl_analysis_breakpoints(session)
        
        # Add custom script if provided
        if args.script and os.path.exists(args.script):
            with open(args.script, 'r') as f:
                session.scripts.extend(f.read().split('\n'))
        
        # Run session
        result = lldb.run_debug_session(session, args.interactive)
        
        if not args.interactive:
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()