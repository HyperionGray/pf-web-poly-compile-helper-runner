#!/bin/bash
# Script to generate a WASM hook module template

set -e

OUTPUT="${1:-hook.wat}"

mkdir -p "$(dirname "$OUTPUT")"

cat > "$OUTPUT" << 'EOF'
(module
  ;; Import functions from the host environment
  (import "env" "log" (func $log (param i32)))
  
  ;; Memory for hook data
  (memory (export "memory") 1)
  
  ;; Hook function that wraps another function
  (func $hook_wrapper (param $value i32) (result i32)
    ;; Log the input
    local.get $value
    call $log
    
    ;; Do some processing
    local.get $value
    i32.const 1
    i32.add
    
    ;; Return modified value
  )
  
  (export "hook_wrapper" (func $hook_wrapper))
)
EOF

echo "Created WASM hook template: $OUTPUT"
echo "Compile with: wat2wasm $OUTPUT -o ${OUTPUT%.wat}.wasm"
