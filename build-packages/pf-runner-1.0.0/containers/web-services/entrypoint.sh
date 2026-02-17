#!/bin/bash
set -e

# Default configuration
DEFAULT_PORT=8080
DEFAULT_ROOT="/app/web"

# Parse environment variables
PORT=${PORT:-$DEFAULT_PORT}
ROOT=${ROOT:-$DEFAULT_ROOT}
MODE=${MODE:-"api-server"}

# Ensure web directory exists
mkdir -p "$ROOT"

# Function to start API server
start_api_server() {
    echo "Starting API server on port $PORT with root $ROOT"
    exec node tools/api-server.mjs "$ROOT" "$PORT"
}

# Function to start static server only
start_static_server() {
    echo "Starting static server on port $PORT with root $ROOT"
    exec node tools/static-server.mjs "$ROOT" "$PORT"
}

# Function to run development mode
start_dev_mode() {
    echo "Starting development mode with hot reload"
    export NODE_ENV=development
    exec node tools/api-server.mjs "$ROOT" "$PORT"
}

# Function to show help
show_help() {
    cat << EOF
Web Services Container

Usage: $0 [COMMAND]

Commands:
    api-server      Start the full API server with WebSocket support (default)
    static-server   Start static file server only
    dev             Start in development mode with hot reload
    bash            Start interactive bash shell
    help            Show this help message

Environment Variables:
    PORT            Server port (default: $DEFAULT_PORT)
    ROOT            Web root directory (default: $DEFAULT_ROOT)
    NODE_ENV        Node.js environment (production/development)

Examples:
    # Start API server on port 3000
    PORT=3000 $0 api-server
    
    # Start static server with custom root
    ROOT=/custom/path $0 static-server
    
    # Development mode
    $0 dev
EOF
}

# Handle different commands
case "${1:-api-server}" in
    "api-server")
        start_api_server
        ;;
    "static-server")
        start_static_server
        ;;
    "dev")
        start_dev_mode
        ;;
    "bash")
        exec /bin/bash
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac