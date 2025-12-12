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
