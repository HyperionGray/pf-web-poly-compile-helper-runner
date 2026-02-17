#!/usr/bin/env python3
"""
Runtime injection tool for injecting shared libraries into running processes.
This tool uses ptrace and dlopen to inject libraries at runtime.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

try:
    import frida
    FRIDA_AVAILABLE = True
except ImportError:
    FRIDA_AVAILABLE = False

def inject_with_frida(pid, library_path):
    """Inject library using Frida (preferred method)"""
    if not FRIDA_AVAILABLE:
        raise ImportError("Frida not available. Install with: pip3 install frida-tools")
    
    print(f"Injecting {library_path} into process {pid} using Frida...")
    
    try:
        # Attach to the process
        session = frida.attach(int(pid))
        
        # JavaScript code to inject the library
        script_code = f"""
        var dlopen = Module.findExportByName(null, "dlopen");
        var dlerror = Module.findExportByName(null, "dlerror");
        
        if (dlopen && dlerror) {{
            var library_path = Memory.allocUtf8String("{library_path}");
            var handle = new NativeFunction(dlopen, 'pointer', ['pointer', 'int'])(library_path, 2); // RTLD_NOW
            
            if (handle.isNull()) {{
                var error = new NativeFunction(dlerror, 'pointer', [])();
                var error_str = Memory.readUtf8String(error);
                console.log("dlopen failed: " + error_str);
            }} else {{
                console.log("Library injected successfully!");
                console.log("Handle: " + handle);
            }}
        }} else {{
            console.log("dlopen/dlerror not found");
        }}
        """
        
        # Create and load the script
        script = session.create_script(script_code)
        script.load()
        
        # Wait a moment for injection to complete
        time.sleep(1)
        
        # Detach
        session.detach()
        
        print("Frida injection completed")
        
    except frida.ProcessNotFoundError:
        raise RuntimeError(f"Process {pid} not found")
    except Exception as e:
        raise RuntimeError(f"Frida injection failed: {e}")

def inject_with_gdb(pid, library_path):
    """Inject library using GDB"""
    print(f"Injecting {library_path} into process {pid} using GDB...")
    
    # Check if GDB is available
    try:
        subprocess.run(['gdb', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("GDB not found. Install with: sudo apt-get install gdb")
    
    # Create GDB script
    gdb_script = f"""
set confirm off
attach {pid}
call (void*)dlopen("{os.path.abspath(library_path)}", 2)
detach
quit
"""
    
    # Write script to temporary file
    script_path = f"/tmp/inject_{pid}.gdb"
    with open(script_path, 'w') as f:
        f.write(gdb_script)
    
    try:
        # Run GDB with the script
        result = subprocess.run([
            'gdb', '-batch', '-x', script_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("GDB injection completed")
            if "dlopen" in result.stdout:
                print("Library loaded successfully")
        else:
            raise RuntimeError(f"GDB injection failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        raise RuntimeError("GDB injection timed out")
    finally:
        # Clean up script file
        try:
            os.unlink(script_path)
        except:
            pass

def inject_with_proc_mem(pid, library_path):
    """Inject library using /proc/mem manipulation (Linux only)"""
    print(f"Injecting {library_path} into process {pid} using /proc/mem...")
    print("Warning: This method is experimental and may be unstable")
    
    # This is a complex method that requires:
    # 1. Finding dlopen in the target process
    # 2. Allocating memory for the library path
    # 3. Calling dlopen via ptrace or similar
    
    # For now, we'll use a simpler approach with LD_PRELOAD
    print("Using LD_PRELOAD approach instead...")
    
    # Get process command line
    try:
        with open(f"/proc/{pid}/cmdline", 'rb') as f:
            cmdline = f.read().decode('utf-8', errors='ignore').split('\0')
            if cmdline and cmdline[0]:
                print(f"Process command: {' '.join(cmdline)}")
                print("Note: For /proc/mem injection, the process would need to be restarted with LD_PRELOAD")
                print(f"Restart command: LD_PRELOAD={library_path} {' '.join(cmdline)}")
            else:
                print("Could not determine process command line")
    except:
        print("Could not read process information")
    
    raise RuntimeError("Direct /proc/mem injection not implemented - use Frida or GDB methods")

def check_process(pid):
    """Check if process exists and get basic info"""
    try:
        pid = int(pid)
    except ValueError:
        raise ValueError(f"Invalid PID: {pid}")
    
    # Check if process exists
    try:
        os.kill(pid, 0)  # Signal 0 just checks if process exists
    except OSError:
        raise RuntimeError(f"Process {pid} not found or not accessible")
    
    # Get process info
    try:
        with open(f"/proc/{pid}/comm", 'r') as f:
            process_name = f.read().strip()
        print(f"Target process: {process_name} (PID: {pid})")
    except:
        print(f"Target PID: {pid}")
    
    # Check if we can attach (requires same user or root)
    try:
        with open(f"/proc/{pid}/status", 'r') as f:
            status = f.read()
            for line in status.split('\n'):
                if line.startswith('Uid:'):
                    uid_info = line.split()
                    if len(uid_info) > 1:
                        target_uid = uid_info[1]
                        current_uid = str(os.getuid())
                        if target_uid != current_uid and current_uid != '0':
                            print(f"Warning: Target process UID ({target_uid}) differs from current UID ({current_uid})")
                            print("You may need root privileges for injection")
                    break
    except:
        pass

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 runtime-inject.py <pid> <library_path>")
        print("")
        print("This tool injects a shared library into a running process.")
        print("The library will be loaded using dlopen() at runtime.")
        print("")
        print("Examples:")
        print("  python3 runtime-inject.py 1234 ./payload.so")
        print("  python3 runtime-inject.py $(pidof myapp) /tmp/injected.so")
        print("")
        print("Requirements:")
        print("  - Target process must be accessible (same user or root)")
        print("  - Library must be compiled as a shared library (.so)")
        print("  - Frida or GDB must be installed for injection")
        sys.exit(1)
    
    pid = sys.argv[1]
    library_path = sys.argv[2]
    
    # Validate inputs
    if not os.path.exists(library_path):
        print(f"Error: Library not found: {library_path}")
        sys.exit(1)
    
    # Check if it's a shared library
    try:
        result = subprocess.run(['file', library_path], capture_output=True, text=True)
        if 'shared object' not in result.stdout.lower():
            print(f"Warning: {library_path} may not be a shared library")
            print(f"File type: {result.stdout.strip()}")
    except:
        pass
    
    # Check target process
    try:
        check_process(pid)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Try injection methods in order of preference
    methods = [
        ("Frida", inject_with_frida),
        ("GDB", inject_with_gdb),
        ("/proc/mem", inject_with_proc_mem)
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"\nTrying {method_name} method...")
            method_func(pid, library_path)
            print(f"Success! Library injected using {method_name}")
            break
        except Exception as e:
            print(f"{method_name} method failed: {e}")
            continue
    else:
        print("All injection methods failed!")
        print("\nTroubleshooting:")
        print("1. Make sure you have permission to attach to the process")
        print("2. Install Frida: pip3 install frida-tools")
        print("3. Install GDB: sudo apt-get install gdb")
        print("4. Try running as root if targeting system processes")
        sys.exit(1)
    
    print("\nRuntime injection completed!")
    print("The library should now be loaded in the target process")
    print("\nVerification:")
    print(f"  Check process maps: cat /proc/{pid}/maps | grep {os.path.basename(library_path)}")
    print(f"  Check loaded libraries: lsof -p {pid} | grep {os.path.basename(library_path)}")

if __name__ == "__main__":
    main()