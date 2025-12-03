#!/usr/bin/env bash
# Setup VMKit for PE execution and microVM fuzzing swarm

echo "[*] VMKit Setup for PE Execution and MicroVM Swarm Fuzzing"
echo ""

# Check for VMKit repository
VMKIT_PATH="${VMKIT_PATH:-../HGWS/VMkit}"
if [ -d "$VMKIT_PATH" ]; then
    echo "[*] VMKit repository found at: $VMKIT_PATH"
    VMKIT_AVAILABLE=true
else
    echo "[!] VMKit repository not found at: $VMKIT_PATH"
    echo "[!] Please clone HyperionGray/HGWS repository or set VMKIT_PATH"
    VMKIT_AVAILABLE=false
fi

echo ""
echo "VMKit integration provides:"
echo "  - Lightweight microVM infrastructure for PE execution"
echo "  - Hardware passthrough with --all-the-passthru option"
echo "  - VM lifecycle management for container-like operations"
echo "  - Parallel PE execution across multiple VMs"
echo "  - Result collection and analysis pipeline"
echo ""

if [ "$VMKIT_AVAILABLE" = true ]; then
    echo "[*] Setting up VMKit environment..."
    
    # Create VMKit configuration for PE execution
    cat > /tmp/vmkit-pe-config.yaml << 'EOF'
# VMKit Configuration for PE Execution
pe_execution:
  default_vm_config:
    memory: 2048
    cpus: 2
    disk_size: 20G
    passthrough: all
  
  windows_server_core:
    base_image: "windows-server-core-2022"
    memory: 2048
    cpus: 2
    timeout: 300
  
  reactos:
    base_image: "reactos-0.4.15"
    memory: 1024
    cpus: 2
    timeout: 300
  
  macos:
    base_image: "macos-monterey"
    memory: 8192
    cpus: 4
    timeout: 600

vm_pool:
  max_concurrent: 10
  cleanup_timeout: 60
  snapshot_enabled: true
EOF
    
    echo "[*] VMKit PE execution configuration created"
    
    # Check VMKit installation
    if [ -f "$VMKIT_PATH/vmkit" ]; then
        echo "[*] VMKit binary found"
        
        # Test VMKit functionality
        echo "[*] Testing VMKit functionality..."
        if "$VMKIT_PATH/vmkit" --version >/dev/null 2>&1; then
            echo "[✓] VMKit is functional"
        else
            echo "[!] VMKit test failed - may need setup"
        fi
    else
        echo "[!] VMKit binary not found - installation may be incomplete"
    fi
    
    # Create VMKit wrapper for PE execution
    cat > ~/.local/bin/vmkit-pe << 'EOF'
#!/bin/bash
# VMKit wrapper for PE execution

VMKIT_PATH="${VMKIT_PATH:-../HGWS/VMkit}"
VMKIT_BIN="$VMKIT_PATH/vmkit"

if [ ! -f "$VMKIT_BIN" ]; then
    echo "Error: VMKit not found at $VMKIT_BIN"
    echo "Set VMKIT_PATH environment variable or install VMKit"
    exit 1
fi

case "$1" in
    "create-pe-vm")
        echo "[VMKit] Creating PE execution VM: $2"
        "$VMKIT_BIN" create --all-the-passthru --config pe-execution "$2"
        ;;
    "execute-pe")
        echo "[VMKit] Executing PE file: $3 in VM: $2"
        "$VMKIT_BIN" exec "$2" --file "$3" --timeout "${4:-300}"
        ;;
    "cleanup-pe-vm")
        echo "[VMKit] Cleaning up PE VM: $2"
        "$VMKIT_BIN" destroy "$2"
        ;;
    *)
        echo "Usage: vmkit-pe {create-pe-vm|execute-pe|cleanup-pe-vm} [args...]"
        echo "  create-pe-vm <vm-name>              Create PE execution VM"
        echo "  execute-pe <vm-name> <pe-file> [timeout]    Execute PE in VM"
        echo "  cleanup-pe-vm <vm-name>             Destroy PE VM"
        exit 1
        ;;
esac
EOF
    
    chmod +x ~/.local/bin/vmkit-pe
    echo "[*] VMKit PE execution wrapper installed to ~/.local/bin/vmkit-pe"
    
else
    echo "[!] VMKit not available - using fallback QEMU implementation"
    echo ""
    echo "To enable VMKit integration:"
    echo "  1. Clone HyperionGray/HGWS repository"
    echo "  2. Build and install VMKit"
    echo "  3. Set VMKIT_PATH environment variable"
    echo "  4. Re-run this setup script"
fi

echo ""
echo "For VM-based PE execution, the system supports:"
echo "  - VMKit with hardware passthrough (preferred)"
echo "  - Direct QEMU with KVM acceleration (fallback)"
echo "  - Firecracker microVMs: https://firecracker-microvm.github.io/"
echo "  - Cloud Hypervisor: https://www.cloudhypervisor.org/"
echo ""

# Check system requirements
echo "[*] Checking system requirements..."

# Check KVM support
if [ -r /dev/kvm ]; then
    echo "[✓] KVM support available"
else
    echo "[!] KVM support not available - will use software emulation"
fi

# Check memory
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -gt 8192 ]; then
    echo "[✓] Sufficient memory available (${TOTAL_MEM}MB)"
else
    echo "[!] Limited memory (${TOTAL_MEM}MB) - may affect VM performance"
fi

# Check CPU cores
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -gt 2 ]; then
    echo "[✓] Sufficient CPU cores available ($CPU_CORES)"
else
    echo "[!] Limited CPU cores ($CPU_CORES) - may affect concurrent VM execution"
fi

echo ""
echo "[*] VMKit setup complete"
echo ""
echo "Next steps:"
echo "  1. Build PE execution containers: pf pe-build-all"
echo "  2. Prepare VM templates: pf pe-prepare-windows && pf pe-prepare-reactos"
echo "  3. Test PE execution: pf pe-execute pe_file=./test.exe"
echo ""
echo "See Pfyfile.pe-execution.pf for all available commands"
