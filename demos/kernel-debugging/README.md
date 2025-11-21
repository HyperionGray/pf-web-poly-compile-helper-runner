# Kernel Debugging Demo

This demo showcases the advanced kernel-mode debugging features.

## Quick Demo

Since the repository has a syntax error in the pf_parser.py (pre-existing), we can use the tools directly:

### 1. IOCTL Discovery

```bash
# Discover IOCTLs in a driver
python3 tools/debugging/ioctl/discover_ioctls.py /path/to/driver.ko ./output

# Analyze IOCTL structure
python3 tools/debugging/ioctl/analyze_ioctls.py /path/to/driver.ko

# Fuzz discovered IOCTLs
python3 tools/debugging/ioctl/fuzz_ioctls.py /dev/mydriver ./output/driver_ioctls.json 10000
```

### 2. Firmware Analysis

```bash
# Analyze firmware security
python3 tools/debugging/firmware/analyze_firmware.py firmware.bin
```

### 3. Reversing with LLDB

```bash
# Automated LLDB session
python3 tools/debugging/reversing/lldb_automation.py /path/to/binary

# With custom breakpoints
LLDB_FUNCTIONS="malloc,free" python3 tools/debugging/reversing/lldb_automation.py /path/to/binary
```

### 4. Radare2 Automation

```bash
# Automated analysis with radare2
python3 tools/debugging/reversing/r2_automation.py /path/to/binary
```

### 5. Fast Fuzzing

```bash
# Basic fuzzing
python3 tools/debugging/fuzzing/fast_fuzzer.py /path/to/binary 10000 5
```

### 6. Create Plugins

```bash
# Create radare2 plugin
python3 tools/debugging/plugins/create_r2_plugin.py my_analyzer ./plugins

# Create Binary Ninja plugin
python3 tools/debugging/plugins/create_binja_plugin.py my_analyzer ./plugins
```

## Features Implemented

### IOCTL Tools
- **discover_ioctls.py**: Multi-method IOCTL discovery (strings, objdump, radare2)
- **analyze_ioctls.py**: Structure size analysis and validation detection
- **fuzz_ioctls.py**: IOCTL fuzzer with multiple strategies

### Firmware Tools
- **analyze_firmware.py**: Security analysis, entropy calculation, string extraction

### Reversing Tools
- **lldb_automation.py**: Automated LLDB debugging with breakpoints
- **r2_automation.py**: Radare2 automation with r2pipe
- **auto_breakpoints.py**: Generate conditional breakpoint scripts
- **control_flow.py**: CFG extraction stub
- **ghidra_headless.sh**: Ghidra headless wrapper

### Vulnerability Tools
- **scan_vulnerabilities.py**: Vulnerability pattern scanning
- **heuristic_analysis.py**: Heuristic-based weakness detection
- **kernel_security_check.py**: Kernel module security checks

### Fuzzing Tools
- **fast_fuzzer.py**: High-speed fuzzer with crash detection
- **parallel_fuzzer.py**: Multi-core fuzzing
- **run_syzkaller.sh**: Syzkaller integration
- **run_kfuzz.sh**: KFuzz wrapper

### MicroVM Tools
- **setup_vmkit.sh**: VMKit environment setup
- **deploy_swarm.py**: Deploy to microVM swarm
- **monitor_swarm.py**: Monitor fuzzing progress
- **collect_results.py**: Collect swarm results

### Plugin Tools
- **create_r2_plugin.py**: Generate radare2 plugin templates
- **create_binja_plugin.py**: Generate Binary Ninja plugin templates
- **install_r2_plugin.sh**: Install radare2 plugins
- **install_binja_plugin.sh**: Install Binary Ninja plugins

## Installation

All tools work independently. To install dependencies:

```bash
# Install debugging tools
bash tools/debugging/install-debug-tools.sh

# Install radare2
sudo apt-get install radare2
pip3 install r2pipe

# Install LLDB
sudo apt-get install lldb

# Install firmware tools
sudo apt-get install binwalk flashrom
```

## Documentation

See [`docs/KERNEL-DEBUGGING.md`](../../docs/KERNEL-DEBUGGING.md) for comprehensive documentation.

## Task Definitions

Once the pf_parser.py syntax error is fixed, 50+ debugging tasks will be available via the `pf` command defined in `Pfyfile.debugging.pf`.

## Note on Pre-existing Issue

The pf runner has a syntax error in pf_parser.py line 1353 that exists before our changes. All debugging tools work independently as Python scripts and shell scripts.
