// Integer overflow vulnerability practice binary
// Purpose: Learn integer overflow exploitation
// Vulnerability: Integer overflow in size calculation

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void secret_access() {
    printf("\n🎯 SECRET ACCESS GRANTED! 🎯\n");
    printf("Integer overflow exploitation successful!\n");
    system("/bin/sh");
}

void allocate_buffer(unsigned int count, unsigned int size) {
    printf("\n=== Buffer Allocation ===\n");
    printf("Count: %u\n", count);
    printf("Size per element: %u\n", size);
    
    // VULNERABILITY: Integer overflow in multiplication
    unsigned int total = count * size;
    printf("Total size calculated: %u bytes\n", total);
    
    if (total == 0) {
        printf("❌ Cannot allocate 0 bytes!\n");
        return;
    }
    
    char *buffer = (char*)malloc(total);
    if (!buffer) {
        printf("❌ Allocation failed!\n");
        return;
    }
    
    printf("✓ Allocated buffer at: %p\n", (void*)buffer);
    
    // Fill buffer - this is where overflow can cause heap corruption
    printf("Filling buffer...\n");
    for (unsigned int i = 0; i < count; i++) {
        // VULNERABILITY: Writes beyond allocated buffer if overflow occurred
        memset(buffer + (i * size), 'A', size);
    }
    
    printf("Buffer filled successfully.\n");
    free(buffer);
}

void vulnerable_copy(unsigned int src_len) {
    printf("\n=== String Copy Operation ===\n");
    printf("Source length: %u\n", src_len);
    
    // VULNERABILITY: Adding 1 can overflow
    unsigned int buffer_size = src_len + 1;
    printf("Buffer size (len+1): %u\n", buffer_size);
    
    if (buffer_size == 0) {
        printf("❌ Buffer size overflowed to 0!\n");
        return;
    }
    
    char *buffer = (char*)malloc(buffer_size);
    if (!buffer) {
        printf("❌ Allocation failed!\n");
        return;
    }
    
    printf("✓ Allocated %u bytes at %p\n", buffer_size, (void*)buffer);
    
    // Create source string (if overflow, buffer is tiny but src is huge)
    char *src = (char*)malloc(src_len);
    if (src) {
        memset(src, 'B', src_len);
        memcpy(buffer, src, src_len);  // VULNERABILITY: Overflow write
        buffer[src_len] = '\0';
        free(src);
    }
    
    free(buffer);
}

int main(int argc, char *argv[]) {
    printf("=== Integer Overflow Practice ===\n");
    printf("Secret function at: %p\n", (void*)secret_access);
    
    if (argc < 2) {
        printf("\nUsage: %s <command> [args]\n", argv[0]);
        printf("Commands:\n");
        printf("  alloc <count> <size>  - Allocate count*size bytes\n");
        printf("  copy <length>         - Copy string of length\n");
        printf("\nPractice objectives:\n");
        printf("1. Understand integer overflow in size calculations\n");
        printf("2. Trigger overflow: large_count * large_size wraps to small value\n");
        printf("3. Cause heap corruption via undersized allocation\n");
        printf("4. Example: alloc 0x40000000 4 (wraps to 0)\n");
        printf("5. Example: copy 0xFFFFFFFF (len+1 wraps to 0)\n");
        return 1;
    }
    
    if (strcmp(argv[1], "alloc") == 0 && argc > 3) {
        unsigned int count = (unsigned int)strtoul(argv[2], NULL, 0);
        unsigned int size = (unsigned int)strtoul(argv[3], NULL, 0);
        allocate_buffer(count, size);
    } else if (strcmp(argv[1], "copy") == 0 && argc > 2) {
        unsigned int len = (unsigned int)strtoul(argv[2], NULL, 0);
        vulnerable_copy(len);
    } else {
        printf("Invalid command!\n");
    }
    
    return 0;
}
