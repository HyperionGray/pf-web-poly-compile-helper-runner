#!/bin/bash
# Performance Benchmarking for pf Language Parser
# Tests parser performance with various Pfyfile sizes and complexities

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_DIR=$(mktemp -d)

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
    log_test() { echo -e "${BLUE}[BENCHMARK]${NC} $1"; TOTAL_TESTS=$((TOTAL_TESTS + 1)); }
    log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASSED_TESTS=$((PASSED_TESTS + 1)); }
    log_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILED_TESTS=$((FAILED_TESTS + 1)); }
    log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
fi

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Benchmark function
benchmark_parser() {
    local test_name="$1"
    local pf_file="$2"
    local max_time_ms="$3"
    local iterations="${4:-5}"
    
    log_test "$test_name"
    
    if [ ! -f "$pf_file" ]; then
        log_fail "$test_name - File not found: $pf_file"
        return
    fi
    
    local total_time=0
    local min_time=999999999
    local max_time=0
    
    cd "$ROOT_DIR/pf-runner"
    
    for i in $(seq 1 $iterations); do
        start_time=$(date +%s%N)
        if python3 pf_parser.py list --file="$pf_file" >/dev/null 2>&1; then
            end_time=$(date +%s%N)
            duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
            
            total_time=$((total_time + duration))
            
            if [ $duration -lt $min_time ]; then
                min_time=$duration
            fi
            
            if [ $duration -gt $max_time ]; then
                max_time=$duration
            fi
        else
            log_fail "$test_name - Parser failed on iteration $i"
            return
        fi
    done
    
    local avg_time=$((total_time / iterations))
    
    if [ $avg_time -lt $max_time_ms ]; then
        log_pass "$test_name - Avg: ${avg_time}ms, Min: ${min_time}ms, Max: ${max_time}ms (< ${max_time_ms}ms)"
    else
        log_fail "$test_name - Avg: ${avg_time}ms (> ${max_time_ms}ms threshold)"
    fi
}

# Generate test Pfyfiles of various sizes
generate_large_pfyfile() {
    local file="$1"
    local num_tasks="$2"
    
    cat > "$file" << 'EOF'
# Generated large Pfyfile for performance testing
env GLOBAL_VAR="global_value"
env PROJECT_NAME="performance_test"

EOF
    
    for i in $(seq 1 $num_tasks); do
        cat >> "$file" << EOF
task test-task-$i param1="value1" param2="value2" param3="value3"
  describe Performance test task $i with multiple parameters
  env LOCAL_VAR_$i="local_value_$i"
  shell_lang bash
  shell echo "Task $i: \$param1 \$param2 \$param3"
  if \$param1 == "value1"
    shell echo "Condition met for task $i"
    for item in ["item1", "item2", "item3"]
      shell echo "Processing \$item in task $i"
    end
  else
    shell echo "Condition not met for task $i"
  end
  shell echo "Task $i completed"
end

EOF
    done
}

# Generate complex Pfyfile with nested structures
generate_complex_pfyfile() {
    local file="$1"
    
    cat > "$file" << 'EOF'
# Complex Pfyfile with nested structures and all grammar features
env GLOBAL_ENV="global"
env COMPLEX_VAR="complex_value"

task complex-nested-task mode="dev" debug="true" workers="4"
  describe Complex task with nested control flow and all features
  env TASK_ENV="task_value"
  
  if $mode == "dev"
    if $debug == "true"
      shell_lang python
      shell print("Debug mode enabled")
      shell import os; print(f"Workers: {os.environ.get('workers', '1')}")
      
      for lang in ["rust", "c", "python", "javascript"]
        shell_lang bash
        shell echo "Processing language: $lang"
        
        if `which gcc`
          shell echo "GCC available for $lang compilation"
          directory /tmp/build-$lang mode=0755
          
          for opt in ["O0", "O1", "O2", "O3"]
            shell echo "Testing optimization level: $opt"
          end
        else
          shell echo "GCC not available"
        end
      end
      
      packages install build-essential cmake
      service start docker
      
      sync src="/tmp/source" dst="/tmp/dest" recursive verbose
      
      makefile clean all
      cmake -DCMAKE_BUILD_TYPE=Debug
      cargo build --release
      
    else
      shell echo "Debug disabled"
    end
  else
    shell echo "Production mode"
    
    for component in ["frontend", "backend", "database"]
      shell echo "Deploying component: $component"
      
      if $component == "database"
        service start postgresql
        service enable postgresql
      end
    end
  end
  
  shell_lang node
  shell console.log("Task completed successfully")
end

task build-all-languages
  describe Build all supported languages with optimization
  
  for lang in ["rust", "c", "fortran", "wat"]
    for target in ["wasm", "llvm", "asm"]
      if `which emcc` && $target == "wasm"
        shell echo "Building $lang to $target"
        
        for opt_level in ["0", "1", "2", "3"]
          shell echo "Optimization level: $opt_level"
        end
      end
    end
  end
end

task performance-stress-test iterations="1000"
  describe Stress test with many operations
  
  for i in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    shell echo "Iteration $i"
    
    if $i == "5"
      shell echo "Checkpoint at iteration $i"
    end
  end
end
EOF
}

echo "=== pf Parser Performance Benchmarking ==="
echo "Testing parser performance with various Pfyfile sizes and complexities"
echo

cd "$ROOT_DIR"

# Benchmark 1: Current main Pfyfile
benchmark_parser "Main Pfyfile parsing" "Pfyfile.pf" 1000 10

# Benchmark 2: Small Pfyfile (10 tasks)
generate_large_pfyfile "$TEMP_DIR/small.pf" 10
benchmark_parser "Small Pfyfile (10 tasks)" "$TEMP_DIR/small.pf" 500 10

# Benchmark 3: Medium Pfyfile (50 tasks)
generate_large_pfyfile "$TEMP_DIR/medium.pf" 50
benchmark_parser "Medium Pfyfile (50 tasks)" "$TEMP_DIR/medium.pf" 1500 10

# Benchmark 4: Large Pfyfile (100 tasks)
generate_large_pfyfile "$TEMP_DIR/large.pf" 100
benchmark_parser "Large Pfyfile (100 tasks)" "$TEMP_DIR/large.pf" 3000 5

# Benchmark 5: Very large Pfyfile (500 tasks)
generate_large_pfyfile "$TEMP_DIR/very_large.pf" 500
benchmark_parser "Very large Pfyfile (500 tasks)" "$TEMP_DIR/very_large.pf" 10000 3

# Benchmark 6: Complex nested structures
generate_complex_pfyfile "$TEMP_DIR/complex.pf"
benchmark_parser "Complex nested Pfyfile" "$TEMP_DIR/complex.pf" 2000 10

# Benchmark 7: Memory usage test
log_test "Memory usage benchmark"
cd "$ROOT_DIR/pf-runner"

# Generate a very large file for memory testing
generate_large_pfyfile "$TEMP_DIR/memory_test.pf" 1000

# Detect OS - GNU time's -v flag output format differs between Linux and BSD/macOS
OS_TYPE=$(uname -s)
if [ "$OS_TYPE" != "Linux" ]; then
    log_info "Memory usage benchmark - Skipped (GNU time -v format not supported on $OS_TYPE)"
elif command -v /usr/bin/time >/dev/null 2>&1; then
    memory_output=$(/usr/bin/time -v python3 pf_parser.py list --file="$TEMP_DIR/memory_test.pf" 2>&1 >/dev/null)
    max_memory=$(echo "$memory_output" | grep "Maximum resident set size" | awk '{print $6}')
    
    if [ -n "$max_memory" ] && [ "$max_memory" -lt 100000 ]; then # Less than 100MB
        log_pass "Memory usage benchmark - Peak memory: ${max_memory}KB (< 100MB)"
    else
        log_fail "Memory usage benchmark - Peak memory: ${max_memory}KB (> 100MB)"
    fi
elif [ "$os_type" = "Darwin" ]; then
    # macOS: Use /usr/bin/time with different format
    log_info "Memory usage benchmark - Skipping on macOS (GNU time not available)"
else
    log_info "Memory usage benchmark - /usr/bin/time not available or unsupported platform"
fi

# Benchmark 8: Concurrent parsing
log_test "Concurrent parsing benchmark"
cd "$ROOT_DIR/pf-runner"

start_time=$(date +%s%N)
for i in {1..5}; do
    python3 pf_parser.py list --file="$TEMP_DIR/medium.pf" >/dev/null 2>&1 &
done
wait
end_time=$(date +%s%N)
concurrent_duration=$(( (end_time - start_time) / 1000000 ))

if [ $concurrent_duration -lt 5000 ]; then # Less than 5 seconds for 5 concurrent parses
    log_pass "Concurrent parsing benchmark - 5 concurrent parses: ${concurrent_duration}ms"
else
    log_fail "Concurrent parsing benchmark - 5 concurrent parses: ${concurrent_duration}ms (> 5s)"
fi

# Benchmark 9: Grammar complexity stress test
log_test "Grammar complexity stress test"

# Create a file with maximum grammar complexity
cat > "$TEMP_DIR/grammar_stress.pf" << 'EOF'
env STRESS_VAR="stress_value"

task grammar-stress-test param1="value1" param2="value2" param3="value3" param4="value4"
  describe Maximum grammar complexity stress test
  env LOCAL1="local1" LOCAL2="local2" LOCAL3="local3"
  
  shell_lang python
  shell print("Starting stress test")
  
  if $param1 == "value1"
    if $param2 == "value2"
      if $param3 == "value3"
        for lang in ["rust", "c", "python", "javascript", "go", "java"]
          for target in ["wasm", "llvm", "asm", "native"]
            for opt in ["O0", "O1", "O2", "O3", "Os", "Oz"]
              shell echo "Processing $lang -> $target with $opt"
              
              if `which gcc`
                shell_lang bash
                shell echo "GCC available"
                
                directory /tmp/build-$lang-$target-$opt mode=0755
                copy config.conf /tmp/build-$lang-$target-$opt/ mode=0644
                
                packages install build-essential
                service start docker
                
                sync src="/src" dst="/dst" recursive verbose delete
                
                makefile clean all install
                cmake -DCMAKE_BUILD_TYPE=Release
                meson setup builddir
                cargo build --release
                go_build -o output main.go
                configure --prefix=/usr/local
                justfile build
                autobuild
                build_detect
              else
                shell echo "GCC not available"
              end
            end
          end
        end
      end
    end
  end
  
  shell_lang node
  shell console.log("Stress test completed")
end
EOF

cd "$ROOT_DIR/pf-runner"
start_time=$(date +%s%N)
if python3 pf_parser.py list --file="$TEMP_DIR/grammar_stress.pf" >/dev/null 2>&1; then
    end_time=$(date +%s%N)
    stress_duration=$(( (end_time - start_time) / 1000000 ))
    
    if [ $stress_duration -lt 5000 ]; then # Less than 5 seconds
        log_pass "Grammar complexity stress test - ${stress_duration}ms"
    else
        log_fail "Grammar complexity stress test - ${stress_duration}ms (> 5s)"
    fi
else
    log_fail "Grammar complexity stress test - Parser failed"
fi

# Benchmark 10: Include file performance
log_test "Include file performance"

# Create multiple include files
for i in {1..10}; do
    generate_large_pfyfile "$TEMP_DIR/include_$i.pf" 10
done

# Create main file with includes
cat > "$TEMP_DIR/includes_main.pf" << 'EOF'
# Main file with multiple includes
env MAIN_VAR="main_value"

EOF

for i in {1..10}; do
    echo "include $TEMP_DIR/include_$i.pf" >> "$TEMP_DIR/includes_main.pf"
done

cat >> "$TEMP_DIR/includes_main.pf" << 'EOF'

task main-with-includes
  describe Main task with includes
  shell echo "Main task with includes"
end
EOF

cd "$ROOT_DIR/pf-runner"
start_time=$(date +%s%N)
if python3 pf_parser.py list --file="$TEMP_DIR/includes_main.pf" >/dev/null 2>&1; then
    end_time=$(date +%s%N)
    include_duration=$(( (end_time - start_time) / 1000000 ))
    
    if [ $include_duration -lt 3000 ]; then # Less than 3 seconds
        log_pass "Include file performance - ${include_duration}ms"
    else
        log_fail "Include file performance - ${include_duration}ms (> 3s)"
    fi
else
    log_fail "Include file performance - Parser failed"
fi

echo
echo "=== Performance Benchmark Results ==="
echo "Total benchmarks: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All performance benchmarks passed!${NC}"
    echo -e "${GREEN}Parser performance is within acceptable limits.${NC}"
    exit 0
else
    echo -e "${RED}Some performance benchmarks failed!${NC}"
    echo -e "${YELLOW}Consider optimizing parser performance.${NC}"
    exit 1
fi