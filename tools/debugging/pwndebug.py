#!/usr/bin/env python3
"""
pwndebug.py - Interactive debugger wrapper for GDB/LLDB with pwndbg support

Provides a simplified interface for debugging ELF binaries (C/C++, Rust) with
common commands abstracted from underlying debugger differences.
"""

import sys
import os
import subprocess
import shlex
from typing import Optional, List, Dict
import argparse


class Debugger:
    """Base debugger interface"""
    
    def __init__(self, binary: str, args: List[str] = None):
        self.binary = binary
        self.args = args or []
        self.process = None
        
    def info(self) -> Dict[str, str]:
        """Get binary information"""
        result = {}
        
        # Get file type
        try:
            file_out = subprocess.check_output(['file', self.binary], text=True)
            result['type'] = file_out.strip()
        except:
            result['type'] = 'Unknown'
            
        # Get size info
        try:
            size_out = subprocess.check_output(['size', self.binary], text=True)
            result['size'] = size_out.strip()
        except:
            result['size'] = 'Unknown'
            
        return result


class GDBDebugger(Debugger):
    """GDB-specific debugger implementation"""
    
    def __init__(self, binary: str, args: List[str] = None):
        super().__init__(binary, args)
        self.debugger = 'gdb'
        
    def start_interactive(self):
        """Start interactive GDB session"""
        cmd = ['gdb', '--quiet']
        
        # Add initialization commands
        init_cmds = [
            f'file {self.binary}',
        ]
        
        if self.args:
            init_cmds.append(f'set args {" ".join(self.args)}')
            
        for init_cmd in init_cmds:
            cmd.extend(['-ex', init_cmd])
            
        # Execute GDB
        os.execvp('gdb', cmd)


class LLDBDebugger(Debugger):
    """LLDB-specific debugger implementation"""
    
    def __init__(self, binary: str, args: List[str] = None):
        super().__init__(binary, args)
        self.debugger = 'lldb'
        
    def start_interactive(self):
        """Start interactive LLDB session"""
        cmd = ['lldb', self.binary]
        
        if self.args:
            cmd.extend(['--', *self.args])
            
        # Execute LLDB
        os.execvp('lldb', cmd)


class InteractiveShell:
    """Interactive debugging shell with abstracted commands"""
    
    COMMANDS = {
        'info': 'Show binary information',
        'start': 'Start debugging session with selected debugger',
        'gdb': 'Start GDB debugging session',
        'lldb': 'Start LLDB debugging session',
        'help': 'Show available commands',
        'quit': 'Exit the shell',
    }
    
    def __init__(self, binary: str, args: List[str] = None, debugger: str = 'gdb'):
        self.binary = binary
        self.args = args or []
        self.default_debugger = debugger
        
        # Validate binary exists
        if not os.path.exists(binary):
            print(f"Error: Binary '{binary}' not found")
            sys.exit(1)
            
    def show_banner(self):
        """Display welcome banner"""
        print("=" * 70)
        print("  pwndebug - Interactive Debugger Shell")
        print("  ELF Debugging for C/C++/Rust with GDB/LLDB + pwndbg")
        print("=" * 70)
        print(f"\nBinary: {self.binary}")
        if self.args:
            print(f"Args: {' '.join(self.args)}")
        print(f"Default debugger: {self.default_debugger}")
        print("\nType 'help' for available commands, 'start' to begin debugging\n")
        
    def show_help(self):
        """Display help information"""
        print("\nAvailable commands:")
        print("-" * 50)
        for cmd, desc in self.COMMANDS.items():
            print(f"  {cmd:12} - {desc}")
        print()
        
    def show_info(self):
        """Show binary information"""
        print("\n" + "=" * 50)
        print("Binary Information")
        print("=" * 50)
        
        dbg = GDBDebugger(self.binary, self.args)
        info = dbg.info()
        
        for key, value in info.items():
            print(f"\n{key.upper()}:")
            print(value)
            
        # Check for debug symbols
        try:
            nm_out = subprocess.run(['nm', '-D', self.binary], 
                                  capture_output=True, text=True)
            has_symbols = nm_out.returncode == 0 and nm_out.stdout
            print(f"\nDynamic Symbols: {'Yes' if has_symbols else 'No'}")
        except:
            pass
            
        # Check for security features
        try:
            checksec = subprocess.run(['checksec', '--file', self.binary],
                                    capture_output=True, text=True)
            if checksec.returncode == 0:
                print("\nSecurity Features:")
                print(checksec.stdout)
        except:
            print("\n(Install 'checksec' for security feature analysis)")
            
        print("=" * 50)
        print()
        
    def start_debugger(self, debugger_type: Optional[str] = None):
        """Start debugging session"""
        dbg_type = debugger_type or self.default_debugger
        
        print(f"\nStarting {dbg_type.upper()} debugging session...")
        print(f"Binary: {self.binary}")
        if self.args:
            print(f"Args: {' '.join(self.args)}")
        print()
        
        if dbg_type == 'gdb':
            debugger = GDBDebugger(self.binary, self.args)
        elif dbg_type == 'lldb':
            debugger = LLDBDebugger(self.binary, self.args)
        else:
            print(f"Unknown debugger: {dbg_type}")
            return
            
        # This will replace the current process
        debugger.start_interactive()
        
    def run(self):
        """Run the interactive shell"""
        self.show_banner()
        
        while True:
            try:
                user_input = input("pwndebug> ").strip()
                
                if not user_input:
                    continue
                    
                cmd = user_input.lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    print("Exiting...")
                    break
                elif cmd == 'help':
                    self.show_help()
                elif cmd == 'info':
                    self.show_info()
                elif cmd == 'start':
                    self.start_debugger()
                    # If we get here, debugger exited
                    print("\nDebugger session ended. Type 'start' to debug again.\n")
                elif cmd == 'gdb':
                    self.start_debugger('gdb')
                    print("\nDebugger session ended. Type 'start' to debug again.\n")
                elif cmd == 'lldb':
                    self.start_debugger('lldb')
                    print("\nDebugger session ended. Type 'start' to debug again.\n")
                else:
                    print(f"Unknown command: {user_input}")
                    print("Type 'help' for available commands")
                    
            except EOFError:
                print("\nExiting...")
                break
            except KeyboardInterrupt:
                print("\n\nUse 'quit' to exit")
                continue


def main():
    parser = argparse.ArgumentParser(
        description='Interactive debugger for ELF binaries (C/C++/Rust)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./myprogram                    # Debug with default (gdb)
  %(prog)s ./myprogram arg1 arg2          # Debug with arguments
  %(prog)s -d lldb ./myprogram            # Use LLDB instead
  %(prog)s --info ./myprogram             # Just show binary info
        """
    )
    
    parser.add_argument('binary', help='Path to ELF binary to debug')
    parser.add_argument('args', nargs='*', help='Arguments to pass to the program')
    parser.add_argument('-d', '--debugger', choices=['gdb', 'lldb'], 
                       default='gdb', help='Debugger to use (default: gdb)')
    parser.add_argument('--info', action='store_true',
                       help='Show binary information and exit')
    parser.add_argument('--direct', action='store_true',
                       help='Skip interactive shell and start debugger directly')
    
    args = parser.parse_args()
    
    # Just show info and exit
    if args.info:
        shell = InteractiveShell(args.binary, args.args, args.debugger)
        shell.show_info()
        return
        
    # Direct debugger start
    if args.direct:
        shell = InteractiveShell(args.binary, args.args, args.debugger)
        shell.start_debugger()
        return
        
    # Interactive shell
    shell = InteractiveShell(args.binary, args.args, args.debugger)
    shell.run()


if __name__ == '__main__':
    main()
