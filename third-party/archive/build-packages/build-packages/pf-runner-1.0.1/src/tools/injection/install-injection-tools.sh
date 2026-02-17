#!/bin/bash
# Installation script for binary injection tools

set -e

echo "Installing binary injection tools..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "Warning: Unsupported OS type: $OSTYPE"
    OS="unknown"
fi

echo "Detected OS: $OS"

# Install system dependencies
if [[ "$OS" == "linux" ]]; then
    echo "Installing Linux dependencies..."
    
    # Check if running as root or with sudo
    if [[ $EUID -eq 0 ]] || sudo -n true 2>/dev/null; then
        # Essential tools for binary manipulation
        sudo apt-get update -qq
        sudo apt-get install -y \
            binutils \
            gdb \
            strace \
            ltrace \
            objdump \
            readelf \
            hexdump \
            patchelf \
            python3-dev \
            python3-pip \
            build-essential \
            libc6-dev \
            gcc-multilib \
            g++-multilib
        
        # Install checksec if available
        sudo apt-get install -y pax-utils 2>/dev/null || echo "pax-utils not available, skipping checksec"
        
        echo "Linux dependencies installed successfully"
    else
        echo "Warning: No sudo access. Please install dependencies manually:"
        echo "  sudo apt-get install binutils gdb strace ltrace patchelf python3-dev python3-pip build-essential"
    fi
    
elif [[ "$OS" == "macos" ]]; then
    echo "Installing macOS dependencies..."
    
    # Check if Homebrew is available
    if command -v brew &> /dev/null; then
        brew install binutils gdb python3
        echo "macOS dependencies installed via Homebrew"
    else
        echo "Warning: Homebrew not found. Please install manually:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "  brew install binutils gdb python3"
    fi
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user \
    pyelftools \
    capstone \
    keystone-engine \
    lief \
    pwntools \
    frida-tools 2>/dev/null || echo "Some Python packages may require additional setup"

# Install WABT (WebAssembly Binary Toolkit) for wasm2c
echo "Installing WABT for WebAssembly support..."
if [[ "$OS" == "linux" ]]; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y wabt 2>/dev/null || echo "WABT not available in repositories, manual installation may be required"
    fi
elif [[ "$OS" == "macos" ]]; then
    if command -v brew &> /dev/null; then
        brew install wabt 2>/dev/null || echo "WABT installation failed, manual installation may be required"
    fi
fi

# Create injection tools directory structure
echo "Setting up injection tools directory structure..."
mkdir -p tools/injection/{scripts,templates,examples}

# Create basic injection templates
echo "Creating injection templates..."

# C constructor template
cat > tools/injection/templates/constructor.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>

// Constructor function - executed when library is loaded
__attribute__((constructor))
void injected_constructor() {
    printf("[INJECTED] Constructor executed!\n");
    // Add your injection code here
}

// Destructor function - executed when library is unloaded
__attribute__((destructor))
void injected_destructor() {
    printf("[INJECTED] Destructor executed!\n");
    // Add cleanup code here
}

// Example function that can be called from injected code
void injected_function() {
    printf("[INJECTED] Custom function called!\n");
}
EOF

# Rust constructor template
cat > tools/injection/templates/constructor.rs << 'EOF'
use std::ffi::c_void;

// Constructor function - executed when library is loaded
#[ctor::ctor]
fn injected_constructor() {
    println!("[INJECTED] Rust constructor executed!");
    // Add your injection code here
}

// Destructor function - executed when library is unloaded
#[ctor::dtor]
fn injected_destructor() {
    println!("[INJECTED] Rust destructor executed!");
    // Add cleanup code here
}

// Example function that can be called from injected code
#[no_mangle]
pub extern "C" fn injected_function() {
    println!("[INJECTED] Rust function called!");
}

// Required for shared library
#[no_mangle]
pub extern "C" fn _start() {}
EOF

# Fortran constructor template (using ISO_C_BINDING)
cat > tools/injection/templates/constructor.f90 << 'EOF'
module injection_module
    use iso_c_binding
    implicit none
    
contains
    
    ! Constructor-like subroutine
    subroutine injected_constructor() bind(c, name="injected_constructor")
        write(*,*) '[INJECTED] Fortran constructor executed!'
        ! Add your injection code here
    end subroutine injected_constructor
    
    ! Example function
    subroutine injected_function() bind(c, name="injected_function")
        write(*,*) '[INJECTED] Fortran function called!'
    end subroutine injected_function
    
end module injection_module
EOF

echo "Injection tools installation completed!"
echo ""
echo "Available tools:"
echo "  - Binary analysis: objdump, readelf, nm, ldd"
echo "  - Binary patching: patchelf (Linux), install_name_tool (macOS)"
echo "  - Python libraries: pyelftools, capstone, keystone, lief"
echo "  - WebAssembly: wabt (wasm2c)"
echo "  - Templates: tools/injection/templates/"
echo ""
echo "Next steps:"
echo "  1. Run 'pf injection-help' for usage guide"
echo "  2. Try 'pf test-injection-workflow' for a basic test"
echo "  3. See tools/injection/templates/ for injection code examples"