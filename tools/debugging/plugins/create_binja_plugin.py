#!/usr/bin/env python3
"""Create Binary Ninja Plugin Template"""
import sys
from pathlib import Path

def create_binja_plugin(name, output_dir):
    print(f"[*] Creating Binary Ninja plugin: {name}")
    
    output_path = Path(output_dir) / name
    output_path.mkdir(parents=True, exist_ok=True)
    
    plugin_code = f'''"""
{name} - Binary Ninja Plugin
Auto-generated plugin template
"""

from binaryninja import *

def {name}_analysis(bv):
    """Main analysis function"""
    print(f"[*] Running {name} analysis on {{bv.file.filename}}")
    
    # Your analysis code here
    for func in bv.functions:
        print(f"Function: {{func.name}} @ {{hex(func.start)}}")
    
    print(f"[+] Analysis complete")

# Register plugin
PluginCommand.register(
    "{name.replace('_', ' ').title()}",
    "Run {name} analysis",
    {name}_analysis
)
'''
    
    plugin_file = output_path / f"{name}.py"
    with open(plugin_file, 'w') as f:
        f.write(plugin_code)
    
    print(f"[+] Plugin created: {plugin_file}")
    print(f"\nInstall with:")
    print(f"  pf plugin-binja-install plugin={plugin_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <plugin_name> [output_dir]")
        sys.exit(1)
    
    name = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else './plugins'
    create_binja_plugin(name, output)
