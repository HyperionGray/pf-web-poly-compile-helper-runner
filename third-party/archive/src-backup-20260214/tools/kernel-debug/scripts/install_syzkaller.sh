#!/bin/bash
"""
Syzkaller Installation Script

Installs and configures Syzkaller for kernel fuzzing integration.
"""

set -e

SYZKALLER_VERSION="latest"
INSTALL_DIR="/opt/syzkaller"
GO_VERSION="1.21.0"

echo "Installing Syzkaller for kernel fuzzing..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons"
   echo "Run as regular user with sudo access"
   exit 1
fi

# Install Go if not present
if ! command -v go &> /dev/null; then
    echo "Installing Go ${GO_VERSION}..."
    wget -q "https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz"
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
    rm "go${GO_VERSION}.linux-amd64.tar.gz"
    
    # Add Go to PATH
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
fi

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    git \
    qemu-system-x86 \
    qemu-utils \
    debootstrap \
    flex \
    bison \
    libelf-dev \
    libssl-dev \
    bc

# Create installation directory
sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# Clone Syzkaller
echo "Cloning Syzkaller..."
cd "$INSTALL_DIR"
if [ ! -d "syzkaller" ]; then
    git clone https://github.com/google/syzkaller.git
fi

cd syzkaller

# Build Syzkaller
echo "Building Syzkaller..."
make

# Create configuration template
echo "Creating configuration template..."
cat > syzkaller.cfg << EOF
{
    "target": "linux/amd64",
    "http": "127.0.0.1:56741",
    "workdir": "$INSTALL_DIR/workdir",
    "kernel_obj": "/path/to/kernel/build",
    "image": "/path/to/rootfs.img",
    "sshkey": "/path/to/ssh/key",
    "syzkaller": "$INSTALL_DIR/syzkaller",
    "procs": 8,
    "type": "qemu",
    "vm": {
        "count": 4,
        "kernel": "/path/to/bzImage",
        "cpu": 2,
        "mem": 2048
    }
}
EOF

# Create helper scripts
echo "Creating helper scripts..."

# Syzkaller runner script
cat > run_syzkaller.sh << 'EOF'
#!/bin/bash
# Syzkaller runner script

CONFIG_FILE="${1:-syzkaller.cfg}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found: $CONFIG_FILE"
    echo "Please create a configuration file or specify path"
    exit 1
fi

echo "Starting Syzkaller with config: $CONFIG_FILE"
./bin/syz-manager -config="$CONFIG_FILE"
EOF

chmod +x run_syzkaller.sh

# Kernel build helper
cat > build_kernel.sh << 'EOF'
#!/bin/bash
# Kernel build helper for Syzkaller

KERNEL_DIR="${1:-/usr/src/linux}"
CONFIG_FILE="${2:-syzkaller.config}"

if [ ! -d "$KERNEL_DIR" ]; then
    echo "Kernel directory not found: $KERNEL_DIR"
    exit 1
fi

cd "$KERNEL_DIR"

# Copy Syzkaller kernel config if available
if [ -f "$INSTALL_DIR/syzkaller/dashboard/config/linux/upstream-kasan.config" ]; then
    cp "$INSTALL_DIR/syzkaller/dashboard/config/linux/upstream-kasan.config" .config
else
    # Use default config with debugging enabled
    make defconfig
    
    # Enable debugging options
    scripts/config --enable CONFIG_KASAN
    scripts/config --enable CONFIG_KASAN_INLINE
    scripts/config --enable CONFIG_KCOV
    scripts/config --enable CONFIG_DEBUG_INFO
    scripts/config --enable CONFIG_KALLSYMS_ALL
    scripts/config --enable CONFIG_NAMESPACES
    scripts/config --enable CONFIG_UTS_NS
    scripts/config --enable CONFIG_IPC_NS
    scripts/config --enable CONFIG_PID_NS
    scripts/config --enable CONFIG_NET_NS
    scripts/config --enable CONFIG_USER_NS
    scripts/config --enable CONFIG_CGROUP_PIDS
    scripts/config --enable CONFIG_MEMCG
fi

# Build kernel
make -j$(nproc)

echo "Kernel built successfully"
echo "bzImage: arch/x86/boot/bzImage"
echo "vmlinux: vmlinux"
EOF

chmod +x build_kernel.sh

# Create rootfs helper
cat > create_rootfs.sh << 'EOF'
#!/bin/bash
# Create minimal rootfs for Syzkaller

ROOTFS_DIR="rootfs"
ROOTFS_IMG="rootfs.img"
ROOTFS_SIZE="1G"

echo "Creating rootfs..."

# Create rootfs directory
mkdir -p "$ROOTFS_DIR"

# Create minimal filesystem using debootstrap
sudo debootstrap --variant=minbase focal "$ROOTFS_DIR" http://archive.ubuntu.com/ubuntu/

# Configure rootfs
sudo chroot "$ROOTFS_DIR" /bin/bash << 'CHROOT_EOF'
# Set root password
echo 'root:root' | chpasswd

# Enable SSH
apt-get update
apt-get install -y openssh-server
systemctl enable ssh

# Create SSH key for Syzkaller
mkdir -p /root/.ssh
ssh-keygen -t rsa -b 2048 -f /root/.ssh/id_rsa -N ""
cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Configure network
cat > /etc/netplan/01-netcfg.yaml << EOF
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
EOF

# Install useful tools
apt-get install -y \
    strace \
    gdb \
    vim \
    net-tools \
    tcpdump

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*
CHROOT_EOF

# Create disk image
echo "Creating disk image..."
dd if=/dev/zero of="$ROOTFS_IMG" bs=1 count=0 seek="$ROOTFS_SIZE"
mkfs.ext4 -F "$ROOTFS_IMG"

# Mount and copy rootfs
mkdir -p mnt
sudo mount -o loop "$ROOTFS_IMG" mnt
sudo cp -a "$ROOTFS_DIR"/* mnt/
sudo umount mnt
rmdir mnt

# Copy SSH key for Syzkaller
sudo cp "$ROOTFS_DIR/root/.ssh/id_rsa" syzkaller_key
sudo chown $USER:$USER syzkaller_key

echo "Rootfs created: $ROOTFS_IMG"
echo "SSH key: syzkaller_key"
EOF

chmod +x create_rootfs.sh

# Create integration script for pf-runner
cat > pf_syzkaller_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Syzkaller integration for pf-runner kernel debugging
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def run_syzkaller_campaign(config_file, duration=3600):
    """Run Syzkaller fuzzing campaign"""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    print(f"Starting Syzkaller campaign for {duration} seconds...")
    
    # Start Syzkaller
    process = subprocess.Popen([
        './bin/syz-manager',
        f'-config={config_file}'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for specified duration
        time.sleep(duration)
        
        # Terminate Syzkaller
        process.terminate()
        process.wait(timeout=30)
        
        return {
            'status': 'completed',
            'duration': duration,
            'returncode': process.returncode
        }
    
    except KeyboardInterrupt:
        print("Campaign interrupted by user")
        process.terminate()
        return {'status': 'interrupted'}
    
    except Exception as e:
        print(f"Error during campaign: {e}")
        process.kill()
        return {'status': 'error', 'error': str(e)}

def collect_results(workdir):
    """Collect Syzkaller results"""
    results = {
        'crashes': [],
        'coverage': {},
        'statistics': {}
    }
    
    workdir_path = Path(workdir)
    
    # Collect crash information
    crashes_dir = workdir_path / 'crashes'
    if crashes_dir.exists():
        for crash_dir in crashes_dir.iterdir():
            if crash_dir.is_dir():
                crash_info = {
                    'title': crash_dir.name,
                    'files': list(crash_dir.glob('*'))
                }
                results['crashes'].append(crash_info)
    
    # Collect coverage information
    coverage_file = workdir_path / 'coverage'
    if coverage_file.exists():
        try:
            with open(coverage_file, 'r') as f:
                results['coverage'] = json.load(f)
        except:
            pass
    
    return results

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Syzkaller Integration')
    parser.add_argument('--config', required=True, help='Syzkaller config file')
    parser.add_argument('--duration', type=int, default=3600, help='Campaign duration')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    # Run campaign
    result = run_syzkaller_campaign(args.config, args.duration)
    
    # Collect results if campaign completed
    if result['status'] == 'completed':
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        workdir = config.get('workdir', './workdir')
        results = collect_results(workdir)
        result['results'] = results
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
    else:
        print(json.dumps(result, indent=2, default=str))
EOF

chmod +x pf_syzkaller_integration.py

echo "Syzkaller installation complete!"
echo ""
echo "Installation directory: $INSTALL_DIR/syzkaller"
echo ""
echo "Next steps:"
echo "1. Build a kernel with debugging enabled: ./build_kernel.sh"
echo "2. Create a rootfs image: ./create_rootfs.sh"
echo "3. Update syzkaller.cfg with correct paths"
echo "4. Run Syzkaller: ./run_syzkaller.sh"
echo ""
echo "For pf-runner integration, use:"
echo "  python3 pf_syzkaller_integration.py --config syzkaller.cfg --duration 3600"