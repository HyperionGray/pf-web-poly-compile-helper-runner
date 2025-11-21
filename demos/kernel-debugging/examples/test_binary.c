#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Example vulnerable function for demonstration
void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // Unsafe - buffer overflow
    printf("Buffer: %s\n", buffer);
}

void safe_function(char *input) {
    char buffer[64];
    strncpy(buffer, input, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
    printf("Buffer: %s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        if (strcmp(argv[1], "--safe") == 0 && argc > 2) {
            safe_function(argv[2]);
        } else {
            vulnerable_function(argv[1]);
        }
    } else {
        printf("Usage: %s <input>\n", argv[0]);
        printf("       %s --safe <input>\n", argv[0]);
    }
    return 0;
}
