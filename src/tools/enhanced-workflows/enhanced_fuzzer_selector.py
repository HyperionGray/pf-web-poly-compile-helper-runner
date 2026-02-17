#!/usr/bin/env python3
"""
Enhanced Fuzzer Selector
Intelligently selects and configures fuzzing tools based on target analysis
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

class EnhancedFuzzerSelector:
    def __init__(self):
        self.available_fuzzers = {
            'afl++': {
                'binary_types': ['elf', 'pe'],
                'languages': ['c', 'cpp'],
                'strengths': ['coverage-guided', 'fast'],
                'command_template': 'afl-fuzz -i {input_dir} -o {output_dir} -- {target} @@'
            },
            'libfuzzer': {
                'binary_types': ['elf'],
                'languages': ['c', 'cpp'],
                'strengths': ['in-process', 'sanitizers'],
                'command_template': '{target} -max_total_time={time} -artifact_prefix={output_dir}/'
            },
            'honggfuzz': {
                'binary_types': ['elf', 'pe'],
                'languages': ['c', 'cpp'],
                'strengths': ['feedback-driven', 'hardware-assisted'],
                'command_template': 'honggfuzz -i {input_dir} -W {output_dir} -- {target} ___FILE___'
            },
            'ffuf': {
                'target_types': ['web'],
                'strengths': ['web-fuzzing', 'fast'],
                'command_template': 'ffuf -w {wordlist} -u {target}/FUZZ -o {output_dir}/results.json'
            },
            'wfuzz': {
                'target_types': ['web'],
                'strengths': ['web-fuzzing', 'flexible'],
                'command_template': 'wfuzz -w {wordlist} -f {output_dir}/results.txt {target}/FUZZ'
            },
            'radamsa': {
                'binary_types': ['any'],
                'strengths': ['mutation', 'simple'],
                'command_template': 'radamsa -o {output_dir}/fuzz_%n {input_file}'
            },
            'boofuzz': {
                'target_types': ['network'],
                'strengths': ['protocol-fuzzing', 'stateful'],
                'command_template': 'python3 {script} --target {target} --port {port}'
            }
        }
    
    def select_fuzzer(self, target_info, preferences=None):
        """Select the best fuzzer based on target analysis"""
        target_type = target_info.get('type', 'unknown')
        target_subtype = target_info.get('subtype')
        properties = target_info.get('properties', {})
        
        scored_fuzzers = []
        
        for fuzzer_name, fuzzer_info in self.available_fuzzers.items():
            score = self._calculate_fuzzer_score(fuzzer_info, target_type, target_subtype, properties)
            if score > 0:
                scored_fuzzers.append((fuzzer_name, fuzzer_info, score))
        
        # Sort by score (highest first)
        scored_fuzzers.sort(key=lambda x: x[2], reverse=True)
        
        return scored_fuzzers
    
    def _calculate_fuzzer_score(self, fuzzer_info, target_type, target_subtype, properties):
        """Calculate compatibility score for a fuzzer"""
        score = 0
        
        # Check target type compatibility
        if 'target_types' in fuzzer_info:
            if target_type in fuzzer_info['target_types']:
                score += 10
            else:
                return 0  # Incompatible
        
        # Check binary type compatibility
        if 'binary_types' in fuzzer_info:
            if target_subtype in fuzzer_info['binary_types'] or 'any' in fuzzer_info['binary_types']:
                score += 8
            elif target_type == 'binary':
                return 0  # Incompatible with binary target
        
        # Check language compatibility
        if 'languages' in fuzzer_info:
            target_language = properties.get('language', properties.get('project_type'))
            if target_language in fuzzer_info['languages']:
                score += 5
        
        # Bonus for specific strengths
        if target_type == 'web' and 'web-fuzzing' in fuzzer_info.get('strengths', []):
            score += 3
        if target_type == 'network' and 'protocol-fuzzing' in fuzzer_info.get('strengths', []):
            score += 3
        if 'coverage-guided' in fuzzer_info.get('strengths', []):
            score += 2
        
        return score
    
    def generate_fuzzing_command(self, fuzzer_name, fuzzer_info, target_info, output_dir='./fuzz_output'):
        """Generate fuzzing command for selected fuzzer"""
        properties = target_info.get('properties', {})
        target_path = properties.get('path', properties.get('url', properties.get('target', '')))
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare command parameters
        params = {
            'target': target_path,
            'output_dir': output_dir,
            'input_dir': self._prepare_input_corpus(target_info, output_dir),
            'time': '3600',  # 1 hour default
            'wordlist': self._select_wordlist(target_info),
            'port': properties.get('port', '80'),
            'script': self._generate_boofuzz_script(target_info, output_dir)
        }
        
        # Handle special cases
        if fuzzer_name == 'radamsa':
            params['input_file'] = self._create_sample_input(target_info, output_dir)
        
        # Generate command
        command_template = fuzzer_info['command_template']
        try:
            command = command_template.format(**params)
            return command
        except KeyError as e:
            return f"Error: Missing parameter {e} for fuzzer {fuzzer_name}"
    
    def _prepare_input_corpus(self, target_info, output_dir):
        """Prepare input corpus for fuzzing"""
        input_dir = os.path.join(output_dir, 'input')
        os.makedirs(input_dir, exist_ok=True)
        
        target_type = target_info.get('type')
        
        if target_type == 'binary':
            # Create basic input files for binary fuzzing
            with open(os.path.join(input_dir, 'sample1.txt'), 'w') as f:
                f.write('Hello World\n')
            with open(os.path.join(input_dir, 'sample2.txt'), 'w') as f:
                f.write('A' * 100 + '\n')
            with open(os.path.join(input_dir, 'sample3.txt'), 'w') as f:
                f.write('{"key": "value"}\n')
        elif target_type == 'web':
            # Create web-specific inputs
            with open(os.path.join(input_dir, 'web_sample.txt'), 'w') as f:
                f.write("admin\ntest\nuser\nroot\n")
        
        return input_dir
    
    def _select_wordlist(self, target_info):
        """Select appropriate wordlist for fuzzing"""
        target_type = target_info.get('type')
        
        # Common wordlist locations
        wordlists = {
            'web': [
                '/usr/share/wordlists/dirb/common.txt',
                '/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt',
                './wordlists/common.txt'
            ],
            'default': [
                '/usr/share/wordlists/rockyou.txt',
                './wordlists/common.txt'
            ]
        }
        
        candidates = wordlists.get(target_type, wordlists['default'])
        
        for wordlist in candidates:
            if os.path.exists(wordlist):
                return wordlist
        
        # Create a basic wordlist if none found
        basic_wordlist = './basic_wordlist.txt'
        with open(basic_wordlist, 'w') as f:
            if target_type == 'web':
                f.write('\n'.join(['admin', 'test', 'user', 'login', 'api', 'config', 'backup']))
            else:
                f.write('\n'.join(['test', 'admin', 'user', 'root', 'password']))
        
        return basic_wordlist
    
    def _create_sample_input(self, target_info, output_dir):
        """Create sample input file for mutation-based fuzzing"""
        input_file = os.path.join(output_dir, 'sample_input.txt')
        
        with open(input_file, 'w') as f:
            f.write('Sample input for fuzzing\n')
            f.write('Line 2 with more data\n')
            f.write('{"json": "data", "number": 42}\n')
        
        return input_file
    
    def _generate_boofuzz_script(self, target_info, output_dir):
        """Generate boofuzz script for protocol fuzzing"""
        script_path = os.path.join(output_dir, 'boofuzz_script.py')
        
        properties = target_info.get('properties', {})
        target_host = properties.get('host', 'localhost')
        target_port = properties.get('port', 80)
        
        script_content = f'''#!/usr/bin/env python3
"""
Generated boofuzz script for protocol fuzzing
"""

from boofuzz import *
import sys

def main():
    target_host = "{target_host}"
    target_port = {target_port}
    
    session = Session(
        target=Target(
            connection=SocketConnection(target_host, target_port, proto='tcp')
        ),
    )
    
    # Define protocol structure (basic HTTP example)
    s_initialize("http_request")
    s_string("GET", fuzzable=False)
    s_delim(" ", fuzzable=False)
    s_string("/", fuzzable=True)
    s_delim(" ", fuzzable=False)
    s_string("HTTP/1.1", fuzzable=False)
    s_static("\\r\\n")
    s_string("Host", fuzzable=False)
    s_delim(": ", fuzzable=False)
    s_string(target_host, fuzzable=True)
    s_static("\\r\\n\\r\\n")
    
    session.connect(s_get("http_request"))
    session.fuzz()

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        return script_path
    
    def run_enhanced_fuzzing(self, target_info, duration=3600, output_dir='./fuzz_output'):
        """Run enhanced fuzzing workflow"""
        print(f"🐛 Starting enhanced fuzzing for target type: {target_info.get('type')}")
        
        # Select best fuzzer
        fuzzer_candidates = self.select_fuzzer(target_info)
        
        if not fuzzer_candidates:
            print("❌ No compatible fuzzers found for this target")
            return False
        
        # Use the top-rated fuzzer
        fuzzer_name, fuzzer_info, score = fuzzer_candidates[0]
        print(f"✅ Selected fuzzer: {fuzzer_name} (score: {score})")
        
        # Generate and display command
        command = self.generate_fuzzing_command(fuzzer_name, fuzzer_info, target_info, output_dir)
        print(f"📝 Fuzzing command: {command}")
        
        # Check if fuzzer is available
        if not self._check_fuzzer_availability(fuzzer_name):
            print(f"⚠️  Fuzzer {fuzzer_name} not found. Install it first.")
            return False
        
        print(f"🚀 Starting fuzzing session (duration: {duration}s)")
        print(f"📁 Output directory: {output_dir}")
        
        # Run the fuzzing command (in a real implementation)
        print("Note: Fuzzing command generated. Run manually or implement subprocess execution.")
        
        return True
    
    def _check_fuzzer_availability(self, fuzzer_name):
        """Check if fuzzer is available on the system"""
        fuzzer_commands = {
            'afl++': 'afl-fuzz',
            'libfuzzer': 'clang',
            'honggfuzz': 'honggfuzz',
            'ffuf': 'ffuf',
            'wfuzz': 'wfuzz',
            'radamsa': 'radamsa',
            'boofuzz': 'python3'
        }
        
        command = fuzzer_commands.get(fuzzer_name, fuzzer_name)
        
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

def main():
    parser = argparse.ArgumentParser(description='Enhanced Fuzzer Selector')
    parser.add_argument('--target-info', required=True, help='Target info JSON file')
    parser.add_argument('--duration', type=int, default=3600, help='Fuzzing duration in seconds')
    parser.add_argument('--output-dir', default='./fuzz_output', help='Output directory')
    parser.add_argument('--list-fuzzers', action='store_true', help='List available fuzzers')
    
    args = parser.parse_args()
    
    selector = EnhancedFuzzerSelector()
    
    if args.list_fuzzers:
        print("Available Enhanced Fuzzers:")
        for name, info in selector.available_fuzzers.items():
            print(f"  {name}: {', '.join(info.get('strengths', []))}")
        return
    
    # Load target info
    with open(args.target_info, 'r') as f:
        target_info = json.load(f)
    
    # Run enhanced fuzzing
    selector.run_enhanced_fuzzing(target_info, args.duration, args.output_dir)

if __name__ == '__main__':
    main()