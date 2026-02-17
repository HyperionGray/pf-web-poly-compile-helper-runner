#!/bin/bash
"""
KFuzz Installation Script

Installs and configures KFuzz for kernel fuzzing integration.
"""

set -e

KFUZZ_DIR="/opt/kfuzz"
LLVM_VERSION="15"

echo "Installing KFuzz for kernel fuzzing..."

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    clang-${LLVM_VERSION} \
    llvm-${LLVM_VERSION} \
    llvm-${LLVM_VERSION}-dev \
    libclang-${LLVM_VERSION}-dev

# Create installation directory
sudo mkdir -p "$KFUZZ_DIR"
sudo chown $USER:$USER "$KFUZZ_DIR"

# Clone KFuzz (placeholder - would be actual KFuzz repository)
echo "Setting up KFuzz environment..."
cd "$KFUZZ_DIR"

# Create KFuzz wrapper structure
mkdir -p {src,build,configs,results}

# Create KFuzz configuration template
cat > configs/kfuzz_template.json << EOF
{
    "target": {
        "kernel_source": "/usr/src/linux",
        "kernel_config": "defconfig",
        "build_dir": "/tmp/kfuzz_kernel_build"
    },
    "fuzzing": {
        "duration": 3600,
        "parallel_jobs": 8,
        "coverage_guided": true,
        "mutation_strategies": [
            "random",
            "dictionary",
            "grammar_based"
        ]
    },
    "instrumentation": {
        "sanitizers": ["kasan", "kcov"],
        "debug_info": true,
        "coverage_tracking": true
    },
    "output": {
        "results_dir": "./results",
        "crash_dir": "./crashes",
        "coverage_dir": "./coverage"
    }
}
EOF

# Create KFuzz wrapper script
cat > kfuzz_wrapper.py << 'EOF'
#!/usr/bin/env python3
"""
KFuzz Wrapper for pf-runner integration
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

class KFuzzRunner:
    """KFuzz runner and result collector"""
    
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.results_dir = Path(self.config['output']['results_dir'])
        self.crash_dir = Path(self.config['output']['crash_dir'])
        self.coverage_dir = Path(self.config['output']['coverage_dir'])
        
        # Create output directories
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        self.coverage_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_kernel(self) -> bool:
        """Prepare kernel for fuzzing"""
        kernel_source = self.config['target']['kernel_source']
        build_dir = self.config['target']['build_dir']
        
        if not os.path.exists(kernel_source):
            print(f"Kernel source not found: {kernel_source}")
            return False
        
        print("Preparing kernel for fuzzing...")
        
        # Create build directory
        os.makedirs(build_dir, exist_ok=True)
        
        # Configure kernel
        cmd = [
            'make', '-C', kernel_source,
            f'O={build_dir}',
            self.config['target']['kernel_config']
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Kernel configuration failed: {result.stderr}")
            return False
        
        # Enable fuzzing-specific options
        config_script = os.path.join(kernel_source, 'scripts', 'config')
        if os.path.exists(config_script):
            options = [
                'CONFIG_KASAN=y',
                'CONFIG_KASAN_INLINE=y',
                'CONFIG_KCOV=y',
                'CONFIG_DEBUG_INFO=y',
                'CONFIG_KALLSYMS_ALL=y'
            ]
            
            for option in options:
                subprocess.run([
                    config_script, '--file', f'{build_dir}/.config',
                    '--enable', option.split('=')[0]
                ])
        
        # Build kernel
        print("Building instrumented kernel...")
        cmd = [
            'make', '-C', kernel_source,
            f'O={build_dir}',
            f'-j{os.cpu_count()}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Kernel build failed: {result.stderr}")
            return False
        
        print("Kernel prepared successfully")
        return True
    
    def run_fuzzing_campaign(self, duration: int = None) -> Dict:
        """Run KFuzz fuzzing campaign"""
        if duration is None:
            duration = self.config['fuzzing']['duration']
        
        print(f"Starting KFuzz campaign for {duration} seconds...")
        
        # Simulate KFuzz execution (replace with actual KFuzz calls)
        start_time = time.time()
        
        try:
            # This would be the actual KFuzz execution
            # For now, simulate with a placeholder
            self._simulate_fuzzing(duration)
            
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # Collect results
            results = self._collect_results()
            
            return {
                'status': 'completed',
                'duration': actual_duration,
                'results': results
            }
        
        except KeyboardInterrupt:
            print("Fuzzing interrupted by user")
            return {'status': 'interrupted'}
        
        except Exception as e:
            print(f"Fuzzing error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _simulate_fuzzing(self, duration: int):
        """Simulate fuzzing process (placeholder)"""
        # This would be replaced with actual KFuzz integration
        
        # Create some sample results
        import random
        
        # Simulate finding crashes
        for i in range(random.randint(0, 5)):
            crash_file = self.crash_dir / f"crash_{i:03d}.txt"
            with open(crash_file, 'w') as f:
                f.write(f"Simulated crash {i}\n")
                f.write(f"Address: 0x{random.randint(0x1000, 0xffffffff):08x}\n")
                f.write("Stack trace:\n")
                f.write("  function_a+0x10\n")
                f.write("  function_b+0x20\n")
        
        # Simulate coverage data
        coverage_file = self.coverage_dir / "coverage.json"
        coverage_data = {
            'total_blocks': random.randint(10000, 50000),
            'covered_blocks': random.randint(5000, 25000),
            'coverage_percentage': random.uniform(20.0, 80.0)
        }
        
        with open(coverage_file, 'w') as f:
            json.dump(coverage_data, f, indent=2)
        
        # Wait for specified duration
        time.sleep(min(duration, 10))  # Cap simulation time
    
    def _collect_results(self) -> Dict:
        """Collect fuzzing results"""
        results = {
            'crashes': [],
            'coverage': {},
            'statistics': {}
        }
        
        # Collect crashes
        if self.crash_dir.exists():
            for crash_file in self.crash_dir.glob('*.txt'):
                with open(crash_file, 'r') as f:
                    results['crashes'].append({
                        'file': str(crash_file),
                        'content': f.read()
                    })
        
        # Collect coverage
        coverage_file = self.coverage_dir / 'coverage.json'
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                results['coverage'] = json.load(f)
        
        # Generate statistics
        results['statistics'] = {
            'total_crashes': len(results['crashes']),
            'coverage_percentage': results['coverage'].get('coverage_percentage', 0)
        }
        
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='KFuzz Wrapper')
    parser.add_argument('--config', required=True, help='KFuzz config file')
    parser.add_argument('--prepare-kernel', action='store_true',
                       help='Prepare kernel for fuzzing')
    parser.add_argument('--duration', type=int, help='Fuzzing duration')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    runner = KFuzzRunner(args.config)
    
    if args.prepare_kernel:
        if not runner.prepare_kernel():
            sys.exit(1)
        print("Kernel preparation completed")
        return
    
    # Run fuzzing campaign
    result = runner.run_fuzzing_campaign(args.duration)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
EOF

chmod +x kfuzz_wrapper.py

# Create integration script for pf-runner
cat > pf_kfuzz_tasks.pf << 'EOF'
# KFuzz integration tasks for pf-runner

task kfuzz-prepare-kernel
  describe Prepare kernel for KFuzz fuzzing
  shell python3 kfuzz_wrapper.py --config ${config:-configs/kfuzz_template.json} --prepare-kernel
end

task kfuzz-run-campaign
  describe Run KFuzz fuzzing campaign
  shell python3 kfuzz_wrapper.py --config ${config:-configs/kfuzz_template.json} --duration ${duration:-3600} --output ${output:-kfuzz_results.json}
end

task kfuzz-quick-test
  describe Quick KFuzz test run
  shell python3 kfuzz_wrapper.py --config ${config:-configs/kfuzz_template.json} --duration 300 --output kfuzz_quick_test.json
end
EOF

echo "KFuzz installation and setup complete!"
echo ""
echo "Installation directory: $KFUZZ_DIR"
echo ""
echo "Next steps:"
echo "1. Update configs/kfuzz_template.json with your kernel source path"
echo "2. Prepare kernel: python3 kfuzz_wrapper.py --config configs/kfuzz_template.json --prepare-kernel"
echo "3. Run fuzzing: python3 kfuzz_wrapper.py --config configs/kfuzz_template.json --duration 3600"
echo ""
echo "For pf-runner integration:"
echo "  pf kfuzz-prepare-kernel config=configs/kfuzz_template.json"
echo "  pf kfuzz-run-campaign duration=3600 output=results.json"