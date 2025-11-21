#!/usr/bin/env python3
"""Create Radare2 Plugin Template"""
import sys
from pathlib import Path

def create_r2_plugin(name, output_dir):
    print(f"[*] Creating radare2 plugin: {name}")
    
    output_path = Path(output_dir) / name
    output_path.mkdir(parents=True, exist_ok=True)
    
    plugin_code = f'''#!/usr/bin/env python3
"""
{name} - Radare2 Plugin
Auto-generated plugin template
"""

import r2pipe

class {name.capitalize()}Plugin:
    """Custom radare2 plugin"""
    
    def __init__(self, r2):
        self.r2 = r2
    
    def analyze(self):
        """Main analysis function"""
        print(f"[*] Running {name} analysis...")
        
        # Your analysis code here
        functions = self.r2.cmdj('aflj')
        print(f"[+] Found {{len(functions)}} functions")
        
        return functions

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: {{sys.argv[0]}} <binary>")
        sys.exit(1)
    
    binary = sys.argv[1]
    r2 = r2pipe.open(binary)
    
    plugin = {name.capitalize()}Plugin(r2)
    results = plugin.analyze()
    
    r2.quit()

if __name__ == '__main__':
    main()
'''
    
    plugin_file = output_path / f"{name}.py"
    with open(plugin_file, 'w') as f:
        f.write(plugin_code)
    
    print(f"[+] Plugin created: {plugin_file}")
    print(f"\nInstall with:")
    print(f"  pf plugin-radare2-install plugin={plugin_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <plugin_name> [output_dir]")
        sys.exit(1)
    
    name = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else './plugins'
    create_r2_plugin(name, output)
