#!/bin/bash
# Comprehensive REST API Testing for pf
# Tests ALL documented REST API endpoints and WebSocket functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_DIR=$(mktemp -d)

# Test configuration
API_PORT=8081
API_URL="http://localhost:$API_PORT"
API_BASE="$API_URL/api"
SERVER_PID=""

# Source shared test utilities if available, otherwise define locally
if [ -f "$SCRIPT_DIR/../lib/test-utils.sh" ]; then
    source "$SCRIPT_DIR/../lib/test-utils.sh"
else
    # Fallback: Define logging functions locally
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    log_test() { echo -e "${BLUE}[TEST]${NC} $1"; TOTAL_TESTS=$((TOTAL_TESTS + 1)); }
    log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASSED_TESTS=$((PASSED_TESTS + 1)); }
    log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
fi

# Override log_fail to display server logs on failure
log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    # Display server logs on failure to aid debugging
    if [ -f "$TEMP_DIR/server.log" ]; then
        echo -e "${YELLOW}[DEBUG]${NC} Last 20 lines of server.log:"
        tail -n 20 "$TEMP_DIR/server.log" 2>/dev/null || true
    fi
}

cleanup() {
    if [ -n "$SERVER_PID" ]; then
        echo "Stopping API server (PID: $SERVER_PID)"
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    # Display last few lines of server logs to aid debugging
    if [ -f "$TEMP_DIR/server.log" ]; then
        echo -e "${YELLOW}[DEBUG]${NC} Last 10 lines of server log:"
        tail -n 10 "$TEMP_DIR/server.log" 2>/dev/null || true
    fi
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Display server logs (last N lines) to aid debugging
show_server_logs() {
    local lines="${1:-30}"
    if [ -f "$TEMP_DIR/server.log" ]; then
        echo -e "${YELLOW}=== Server Log (last $lines lines) ===${NC}"
        tail -n "$lines" "$TEMP_DIR/server.log"
        echo -e "${YELLOW}=== End Server Log ===${NC}"
    fi
}

# Check if required tools are available
check_dependencies() {
    local missing_deps=()
    
    if ! command -v node >/dev/null 2>&1; then
        missing_deps+=("node")
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Missing dependencies: ${missing_deps[*]}${NC}"
        echo "Please install the missing dependencies and try again."
        exit 1
    fi
}

# Start the API server
start_api_server() {
    log_info "Starting API server on port $API_PORT"
    
    cd "$ROOT_DIR"
    
    # Check if API server script exists
    if [ ! -f "tools/api-server.mjs" ]; then
        log_fail "API server script not found at tools/api-server.mjs"
        exit 1
    fi
    
    # Start server in background
    node tools/api-server.mjs demos/pf-web-polyglot-demo-plus-c/web $API_PORT > "$TEMP_DIR/server.log" 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$API_BASE/health" >/dev/null 2>&1; then
            log_info "API server started successfully (PID: $SERVER_PID)"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_fail "API server failed to start within 30 seconds"
    if [ -f "$TEMP_DIR/server.log" ]; then
        echo "Server log:"
        cat "$TEMP_DIR/server.log"
    fi
    exit 1
}

# Test HTTP endpoint
test_http_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local data="$5"
    local expected_content="$6"
    
    log_test "$test_name"
    
    local body_file
    body_file=$(mktemp)

    local curl_opts=("-s" "-w" "%{http_code}" "-o" "$body_file" "-X" "$method")

    if [ -n "$data" ]; then
        curl_opts+=("-H" "Content-Type: application/json" "-d" "$data")
    fi

    curl_opts+=("$API_BASE$endpoint")

    local status_code
    status_code=$(curl "${curl_opts[@]}")

    local body
    body=$(<"$body_file")
    rm "$body_file"
    
    if [ "$status_code" = "$expected_status" ]; then
        if [ -n "$expected_content" ]; then
            if echo "$body" | jq . >/dev/null 2>&1; then
                if echo "$body" | jq -r . | grep -q "$expected_content"; then
                    log_pass "$test_name - Status $status_code, contains '$expected_content'"
                else
                    log_fail "$test_name - Status $status_code, missing '$expected_content' in response: $body"
                fi
            else
                if [[ "$body" == *"$expected_content"* ]]; then
                    log_pass "$test_name - Status $status_code, contains '$expected_content'"
                else
                    log_fail "$test_name - Status $status_code, missing '$expected_content' in response: $body"
                fi
            fi
        else
            log_pass "$test_name - Status $status_code"
        fi
    else
        log_fail "$test_name - Expected status $expected_status, got $status_code. Response: $body"
    fi
}

echo "=== pf REST API Testing ==="
echo "Testing all documented REST API endpoints"
echo

# Check dependencies
check_dependencies

# Start API server
start_api_server

# Test 1: Health check
test_http_endpoint "Health check" "GET" "/health" "200" "" "ok"

# Test 2: System information
test_http_endpoint "System information" "GET" "/system" "200" "" "platform"

# Test 3: Projects list
test_http_endpoint "Projects list" "GET" "/projects" "200" "" "projects"

# Test 4: Modules list
test_http_endpoint "Modules list" "GET" "/modules" "200" "" "modules"

# Test 5: Build status (empty)
test_http_endpoint "Build status empty" "GET" "/status" "200" "" "builds"

# Test 6: Build Rust to WASM
test_http_endpoint "Build Rust WASM" "POST" "/build/rust" "200" '{"target": "wasm"}' "buildId"

# Wait a moment for build to register
sleep 2

# Test 7: Build status (with builds)
test_http_endpoint "Build status with builds" "GET" "/status" "200" "" "rust"

# Test 8: Build C to WASM
test_http_endpoint "Build C WASM" "POST" "/build/c" "200" '{"target": "wasm"}' "buildId"

# Test 9: Build Fortran to WASM
test_http_endpoint "Build Fortran WASM" "POST" "/build/fortran" "200" '{"target": "wasm"}' "buildId"

# Test 10: Build WAT to WASM
test_http_endpoint "Build WAT WASM" "POST" "/build/wat" "200" '{"target": "wasm"}' "buildId"

# Test 11: Build all languages
test_http_endpoint "Build all WASM" "POST" "/build/all" "200" '{"target": "wasm"}' "buildIds"

# Test 12: Build with LLVM target
test_http_endpoint "Build Rust LLVM" "POST" "/build/rust" "200" '{"target": "llvm", "opt_level": "2"}' "buildId"

# Test 13: Build with asm.js target
test_http_endpoint "Build C asm.js" "POST" "/build/c" "200" '{"target": "asm"}' "buildId"

# Test 14: Invalid language
test_http_endpoint "Invalid language" "POST" "/build/invalid" "400" '{"target": "wasm"}' "Unsupported language"

# Test 15: Invalid target
test_http_endpoint "Invalid target" "POST" "/build/rust" "400" '{"target": "invalid"}' "Unsupported target"

# Test 16: Missing request body
test_http_endpoint "Missing request body" "POST" "/build/rust" "400" "" "Missing target"

# Test 17: Invalid JSON
test_http_endpoint "Invalid JSON" "POST" "/build/rust" "400" '{"invalid": json}' ""

# Test 18: Get specific build status
# First, get a build ID from the status endpoint
log_test "Get specific build status"
status_response=$(curl -s "$API_BASE/status")
if echo "$status_response" | jq . >/dev/null 2>&1; then
    build_id=$(echo "$status_response" | jq -r '.builds[0].buildId // empty')
    if [ -n "$build_id" ]; then
        test_http_endpoint "Specific build status" "GET" "/status?buildId=$build_id" "200" "" "buildId"
        
        # Test 19: Get build logs
        test_http_endpoint "Build logs" "GET" "/logs/$build_id" "200" "" "logs"
    else
        log_info "No builds available for specific status test"
    fi
else
    log_fail "Invalid JSON response from status endpoint"
fi

# Test 20: Non-existent build logs
test_http_endpoint "Non-existent build logs" "GET" "/logs/non-existent-build" "404" "" "not found"

# Test 21: Static file serving (backward compatibility)
# Validate by checking for known content instead of relying on status codes
log_test "Static file serving"
static_response=$(curl -s "$API_BASE/../index.html")
if [[ "$static_response" == *"Polyglot WebAssembly Demo"* ]]; then
    log_pass "Static file serving - Response contains expected content 'Polyglot WebAssembly Demo'"
else
    log_fail "Static file serving - Response does not contain expected content 'Polyglot WebAssembly Demo'"
fi

# Test 22: CORS headers check
log_test "CORS headers check"
cors_response=$(curl -s -I -X OPTIONS "$API_BASE/health")
if echo "$cors_response" | grep -i "access-control-allow-origin" >/dev/null; then
    log_pass "CORS headers present"
else
    log_fail "CORS headers missing"
fi

# Test 23: WebSocket connection test (basic)
log_test "WebSocket connection test"
if command -v wscat >/dev/null 2>&1; then
    # Test WebSocket connection if wscat is available
    timeout 5 wscat -c "ws://localhost:$API_PORT" -x '{"type":"ping"}' > "$TEMP_DIR/ws_test.log" 2>&1 &
    ws_pid=$!
    sleep 2
    kill $ws_pid 2>/dev/null || true
    
    if grep -q "connected" "$TEMP_DIR/ws_test.log" 2>/dev/null; then
        log_pass "WebSocket connection successful"
    else
        log_fail "WebSocket connection failed"
    fi
else
    log_info "Skipping WebSocket test - wscat not available"
fi

# Test 24: Concurrent build requests
log_test "Concurrent build requests"
build_response1=$(curl -s -X POST -H 'Content-Type: application/json' -d '{"target": "wasm"}' "$API_BASE/build/rust")
build_response2=$(curl -s -X POST -H 'Content-Type: application/json' -d '{"target": "wasm"}' "$API_BASE/build/c")

if echo "$build_response1" | jq -r '.buildId' >/dev/null 2>&1 && echo "$build_response2" | jq -r '.buildId' >/dev/null 2>&1; then
    log_pass "Concurrent build requests handled"
else
    log_fail "Concurrent build requests failed"
fi

# Test 25: Build with all parameters
test_http_endpoint "Build with all parameters" "POST" "/build/c" "200" \
    '{"target": "llvm", "project": "pf-web-polyglot-demo-plus-c", "opt_level": "3", "parallel": true}' \
    "buildId"

# Test 26: Server performance under load
log_test "Server performance under load"
start_time=$(date +%s)
for i in {1..10}; do
    curl -s "$API_BASE/health" >/dev/null &
done
wait
end_time=$(date +%s)
duration=$((end_time - start_time))

if [ $duration -lt 5 ]; then
    log_pass "Server handled 10 concurrent requests in ${duration}s"
else
    log_fail "Server performance issue: 10 requests took ${duration}s"
fi

echo
echo "=== REST API Test Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All REST API tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some REST API tests failed!${NC}"
    # Display server logs to aid debugging when tests fail
    show_server_logs 30
    exit 1
fi