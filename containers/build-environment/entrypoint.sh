#!/bin/bash
set -e

# Source Emscripten environment
source /opt/emsdk/emsdk_env.sh

# Function to build Rust to WASM
build_rust_wasm() {
    local src_dir="${1:-/workspace/demos/pf-web-polyglot-demo-plus-c/rust}"
    local output_dir="${2:-/workspace/demos/pf-web-polyglot-demo-plus-c/web/wasm}"
    
    echo "Building Rust to WASM..."
    echo "Source: $src_dir"
    echo "Output: $output_dir"
    
    if [ ! -f "$src_dir/Cargo.toml" ]; then
        echo "Error: Cargo.toml not found in $src_dir"
        exit 1
    fi
    
    cd "$src_dir"
    wasm-pack build --target web --out-dir "$output_dir/rust"
    echo "Rust WASM build completed"
}

# Function to build C to WASM
build_c_wasm() {
    local src_file="${1:-/workspace/demos/pf-web-polyglot-demo-plus-c/c/c_trap.c}"
    local output_dir="${2:-/workspace/demos/pf-web-polyglot-demo-plus-c/web/wasm}"
    
    echo "Building C to WASM..."
    echo "Source: $src_file"
    echo "Output: $output_dir"
    
    if [ ! -f "$src_file" ]; then
        echo "Error: C source file not found: $src_file"
        exit 1
    fi
    
    mkdir -p "$output_dir/c"
    emcc "$src_file" -o "$output_dir/c/c_trap.js" \
        -s WASM=1 \
        -s EXPORTED_FUNCTIONS='["_main", "_c_trap"]' \
        -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap"]' \
        -s MODULARIZE=1 \
        -s EXPORT_NAME='CModule'
    echo "C WASM build completed"
}

# Function to build WAT to WASM
build_wat_wasm() {
    local src_file="${1:-/workspace/demos/pf-web-polyglot-demo-plus-c/asm/mini.wat}"
    local output_dir="${2:-/workspace/demos/pf-web-polyglot-demo-plus-c/web/wasm}"
    
    echo "Building WAT to WASM..."
    echo "Source: $src_file"
    echo "Output: $output_dir"
    
    if [ ! -f "$src_file" ]; then
        echo "Error: WAT source file not found: $src_file"
        exit 1
    fi
    
    mkdir -p "$output_dir/wat"
    wat2wasm "$src_file" -o "$output_dir/wat/mini.wasm"
    echo "WAT WASM build completed"
}

# Function to build Fortran to WASM (experimental)
build_fortran_wasm() {
    local src_file="${1:-/workspace/demos/pf-web-polyglot-demo-plus-c/fortran/src/hello.f90}"
    local output_dir="${2:-/workspace/demos/pf-web-polyglot-demo-plus-c/web/wasm}"
    
    echo "Building Fortran to WASM (experimental)..."
    echo "Source: $src_file"
    echo "Output: $output_dir"
    
    if [ ! -f "$src_file" ]; then
        echo "Error: Fortran source file not found: $src_file"
        exit 1
    fi
    
    mkdir -p "$output_dir/fortran"
    # Note: This is experimental and may not work in all cases
    lfortran --backend=wasm "$src_file" -o "$output_dir/fortran/hello.wasm" || \
        echo "Warning: Fortran WASM build failed (experimental feature)"
}

# Function to build all languages
build_all() {
    echo "Building all languages to WASM..."
    build_rust_wasm
    build_c_wasm
    build_wat_wasm
    build_fortran_wasm
    echo "All builds completed"
}

# Function to show build environment info
show_info() {
    echo "Build Environment Information:"
    echo "=============================="
    echo "Rust: $(rustc --version)"
    echo "Cargo: $(cargo --version)"
    echo "wasm-pack: $(wasm-pack --version)"
    echo "Node.js: $(node --version)"
    echo "npm: $(npm --version)"
    echo "Emscripten: $(emcc --version | head -1)"
    echo "WABT wat2wasm: $(wat2wasm --version)"
    echo "LFortran: $(lfortran --version)"
    echo "GCC: $(gcc --version | head -1)"
    echo "Clang: $(clang --version | head -1)"
    echo "LLVM: $(llvm-config --version)"
}

# Function to show help
show_help() {
    cat << EOF
Build Environment Container

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    build-rust      Build Rust to WASM
    build-c         Build C to WASM  
    build-wat       Build WAT to WASM
    build-fortran   Build Fortran to WASM (experimental)
    build-all       Build all languages to WASM
    info            Show build environment information
    bash            Start interactive bash shell
    help            Show this help message

Options:
    --src-dir DIR   Source directory (for Rust builds)
    --src-file FILE Source file (for C, WAT, Fortran builds)
    --output-dir DIR Output directory for WASM files

Environment Variables:
    WORKSPACE       Workspace directory (default: /workspace)
    BUILD_OUTPUT    Build output directory

Examples:
    # Build all languages
    $0 build-all
    
    # Build specific language
    $0 build-rust --src-dir /workspace/my-rust-project
    
    # Build C with custom paths
    $0 build-c --src-file /workspace/my-code.c --output-dir /builds
    
    # Show environment info
    $0 info
EOF
}

# Parse command line arguments
COMMAND="${1:-bash}"
shift || true

while [[ $# -gt 0 ]]; do
    case $1 in
        --src-dir)
            SRC_DIR="$2"
            shift 2
            ;;
        --src-file)
            SRC_FILE="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Handle different commands
case "$COMMAND" in
    "build-rust")
        build_rust_wasm "$SRC_DIR" "$OUTPUT_DIR"
        ;;
    "build-c")
        build_c_wasm "$SRC_FILE" "$OUTPUT_DIR"
        ;;
    "build-wat")
        build_wat_wasm "$SRC_FILE" "$OUTPUT_DIR"
        ;;
    "build-fortran")
        build_fortran_wasm "$SRC_FILE" "$OUTPUT_DIR"
        ;;
    "build-all")
        build_all
        ;;
    "info")
        show_info
        ;;
    "bash")
        exec /bin/bash
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac