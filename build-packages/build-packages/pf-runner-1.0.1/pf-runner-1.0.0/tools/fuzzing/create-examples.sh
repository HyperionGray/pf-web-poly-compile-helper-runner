#!/bin/bash
# Script to create fuzzing examples

mkdir -p demos/fuzzing/examples

# Create vulnerable.c
cat > demos/fuzzing/examples/vulnerable.c << 'CEOF'
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Vulnerable function with multiple bugs for fuzzing demo
int parse_input(const char *input, size_t len) {
    char buffer[64];
    
    // Bug 1: Buffer overflow
    if (len > 10 && input[0] == 'A') {
        memcpy(buffer, input, len);  // Unsafe copy
    }
    
    // Bug 2: Null pointer dereference
    if (len > 5 && memcmp(input, "CRASH", 5) == 0) {
        char *ptr = NULL;
        *ptr = 'X';
    }
    
    // Bug 3: Integer overflow leading to heap overflow
    if (len > 3 && input[0] == 'H' && input[1] == 'E' && input[2] == 'A' && input[3] == 'P') {
        int size = input[4] * 256;  // Can overflow
        char *heap_buf = malloc(size);
        // NOTE: Production code should check if malloc returns NULL!
        // This is intentionally omitted for fuzzing demonstration
        memcpy(heap_buf, input + 5, len - 5);  // Heap overflow
        free(heap_buf);
    }
    
    return 0;
}

#ifdef LIBFUZZER
// libfuzzer harness
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size > 0) {
        parse_input((const char*)data, size);
    }
    return 0;
}
#else
// AFL++ harness (stdin)
int main(int argc, char **argv) {
    char buffer[1024];
    size_t len = fread(buffer, 1, sizeof(buffer), stdin);
    parse_input(buffer, len);
    return 0;
}
#endif
CEOF

# Create README.md
cat > demos/fuzzing/examples/README.md << 'MDEOF'
# Fuzzing Examples

This directory contains example programs for demonstrating fuzzing capabilities.

## vulnerable.c

A deliberately vulnerable program with multiple bug classes:
- Buffer overflow
- Null pointer dereference
- Heap overflow

### Build for libfuzzer:
```bash
pf build-libfuzzer-target source=demos/fuzzing/examples/vulnerable.c output=demos/fuzzing/examples/fuzzer
```

### Build for AFL++:
```bash
pf build-afl-target source=demos/fuzzing/examples/vulnerable.c output=demos/fuzzing/examples/vulnerable_afl
```

### Run libfuzzer:
```bash
pf run-libfuzzer target=demos/fuzzing/examples/fuzzer corpus=demos/fuzzing/corpus time=60
```

### Run AFL++:
```bash
pf afl-fuzz target=demos/fuzzing/examples/vulnerable_afl input=demos/fuzzing/in output=demos/fuzzing/out
```
MDEOF

echo "✅ Created fuzzing examples"
echo "  - demos/fuzzing/examples/vulnerable.c"
echo "  - demos/fuzzing/examples/README.md"
