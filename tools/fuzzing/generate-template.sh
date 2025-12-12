#!/bin/bash
# Script to generate libfuzzer template

OUTPUT_DIR="${output_dir:-./fuzzing}"
OUTPUT_FILE="${output:-${OUTPUT_DIR}/fuzz_target.c}"

mkdir -p "$OUTPUT_DIR"

echo "Generating libfuzzer template at $OUTPUT_FILE..."

cat > "$OUTPUT_FILE" << 'EOF'
#include <stdint.h>
#include <stddef.h>
#include <string.h>

// Your target function to fuzz
// extern int target_function(const uint8_t *data, size_t size);

// libfuzzer entry point
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    
    // Call your target function
    // target_function(data, size);
    
    // Example: Test string functions
    if (size > 10) {
        char buffer[256];
        if (size < sizeof(buffer)) {
            memcpy(buffer, data, size);
            buffer[size] = '\0';
        }
    }
    
    return 0;
}
EOF

echo "✅ Generated libfuzzer template: $OUTPUT_FILE"
echo "Edit the file and implement your fuzzing logic"
echo "Build with: pf build-libfuzzer-target source=$OUTPUT_FILE"
