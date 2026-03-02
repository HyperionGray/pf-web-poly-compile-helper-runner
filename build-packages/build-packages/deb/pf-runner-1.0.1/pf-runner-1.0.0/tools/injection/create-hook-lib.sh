#!/bin/bash
# Script to generate a C hook library template

set -e

OUTPUT="${1:-hook.c}"

mkdir -p "$(dirname "$OUTPUT")"

cat > "$OUTPUT" << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

// Example: Hook malloc to track allocations
void* malloc(size_t size) {
    static void* (*real_malloc)(size_t) = NULL;
    if (!real_malloc) {
        real_malloc = dlsym(RTLD_NEXT, "malloc");
    }
    
    void* ptr = real_malloc(size);
    fprintf(stderr, "[HOOK] malloc(%zu) = %p\n", size, ptr);
    return ptr;
}

// Example: Hook free to track deallocations
void free(void* ptr) {
    static void (*real_free)(void*) = NULL;
    if (!real_free) {
        real_free = dlsym(RTLD_NEXT, "free");
    }
    
    fprintf(stderr, "[HOOK] free(%p)\n", ptr);
    real_free(ptr);
}

// Constructor - runs when library is loaded
__attribute__((constructor))
void init_hooks() {
    fprintf(stderr, "[HOOK] Library loaded, hooks active\n");
}
EOF

echo "Created hook library template: $OUTPUT"
echo "Compile with: pf compile-c-shared-lib source=$OUTPUT output=hook.so"
echo "Use with: pf inject-shared-lib binary=/path/to/program lib=hook.so"
