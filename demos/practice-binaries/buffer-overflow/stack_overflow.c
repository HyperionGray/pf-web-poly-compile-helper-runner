// Stack-based buffer overflow practice binary
// Purpose: Learn to identify and exploit stack buffer overflows
// Vulnerability: strcpy without bounds checking

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void win() {
    printf("\n🎉 SUCCESS! You've reached the win() function!\n");
    printf("This demonstrates successful exploitation of the buffer overflow.\n");
    system("/bin/sh");  // Spawn a shell as reward
}

void vulnerable_function(char *input) {
    char buffer[64];
    printf("Buffer is at: %p\n", (void*)buffer);
    printf("Input length: %zu bytes\n", strlen(input));
    
    // VULNERABILITY: No bounds checking - can overflow buffer
    strcpy(buffer, input);
    
    printf("Buffer contains: %s\n", buffer);
}

void safe_function() {
    printf("This is the safe code path.\n");
}

int main(int argc, char *argv[]) {
    printf("=== Stack Buffer Overflow Practice ===\n");
    printf("Win function is at: %p\n", (void*)win);
    printf("Safe function is at: %p\n", (void*)safe_function);
    
    if (argc < 2) {
        printf("\nUsage: %s <input_string>\n", argv[0]);
        printf("\nPractice objectives:\n");
        printf("1. Debug with GDB/LLDB to see the stack layout\n");
        printf("2. Identify the offset to overwrite return address\n");
        printf("3. Craft payload to redirect execution to win()\n");
        printf("4. Verify exploitation with tools like pwndbg\n");
        return 1;
    }
    
    printf("\nCalling vulnerable function...\n");
    vulnerable_function(argv[1]);
    
    printf("\nProgram completed normally.\n");
    safe_function();
    
    return 0;
}
