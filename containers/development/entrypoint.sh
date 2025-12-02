#!/bin/bash
set -e

# Ensure PATH includes local bin
export PATH="/home/pf/.local/bin:$PATH"
export PYTHONPATH="/workspace/pf-runner:$PYTHONPATH"

# Function to run pf command
run_pf() {
    echo "Running pf command: $*"
    exec pf "$@"
}

# Function to start TUI
start_tui() {
    echo "Starting pf TUI..."
    exec pf tui
}

# Function to list available tasks
list_tasks() {
    echo "Available pf tasks:"
    pf list
}

# Function to show pf environment info
show_info() {
    echo "pf Development Environment Information:"
    echo "======================================"
    echo "pf version: $(pf --version 2>/dev/null || echo 'Not available')"
    echo "Python: $(python3 --version)"
    echo "Fabric: $(python3 -c 'import fabric; print(fabric.__version__)' 2>/dev/null || echo 'Not available')"
    echo "Working directory: $(pwd)"
    echo "Available tasks: $(pf list 2>/dev/null | wc -l || echo 'Unknown')"
    echo ""
    echo "Environment variables:"
    echo "PATH: $PATH"
    echo "PYTHONPATH: $PYTHONPATH"
}

# Function to run development server
start_dev_server() {
    echo "Starting development server..."
    exec pf web-dev
}

# Function to run tests
run_tests() {
    echo "Running tests..."
    exec pf web-test
}

# Function to build all WASM modules
build_all() {
    echo "Building all WASM modules..."
    exec pf web-build-all
}

# Function to show help
show_help() {
    cat << EOF
pf Development Environment Container

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    pf [ARGS]       Run pf command with arguments
    tui             Start interactive TUI
    list            List available pf tasks
    info            Show environment information
    dev-server      Start development server
    test            Run tests
    build-all       Build all WASM modules
    bash            Start interactive bash shell
    help            Show this help message

Examples:
    # Run specific pf task
    $0 pf web-build-rust
    
    # Start TUI
    $0 tui
    
    # List all tasks
    $0 list
    
    # Start development server
    $0 dev-server
    
    # Build everything
    $0 build-all
    
    # Interactive shell
    $0 bash

Environment Variables:
    PF_TASK         Default task to run if no command specified
    PF_ARGS         Default arguments for pf commands
EOF
}

# Handle different commands
COMMAND="${1:-${PF_TASK:-bash}}"

case "$COMMAND" in
    "pf")
        shift
        run_pf "$@"
        ;;
    "tui")
        start_tui
        ;;
    "list")
        list_tasks
        ;;
    "info")
        show_info
        ;;
    "dev-server")
        start_dev_server
        ;;
    "test")
        run_tests
        ;;
    "build-all")
        build_all
        ;;
    "bash")
        exec /bin/bash
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        # If command looks like a pf task, run it
        if pf list 2>/dev/null | grep -q "^$COMMAND$"; then
            echo "Running pf task: $COMMAND"
            shift
            run_pf "$COMMAND" "$@"
        else
            echo "Unknown command: $COMMAND"
            show_help
            exit 1
        fi
        ;;
esac