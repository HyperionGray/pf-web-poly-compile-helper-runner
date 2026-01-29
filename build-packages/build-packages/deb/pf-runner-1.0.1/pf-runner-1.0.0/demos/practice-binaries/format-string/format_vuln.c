// Format string vulnerability practice binary
// Purpose: Learn format string exploitation
// Vulnerability: User-controlled format string in printf

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int secret_value = 0xdeadbeef;
int auth_flag = 0;

void check_auth() {
    if (auth_flag == 1337) {
        printf("\n✅ Authentication successful!\n");
        printf("Secret value: 0x%x\n", secret_value);
        system("/bin/sh");
    } else {
        printf("Access denied. Auth flag: %d\n", auth_flag);
    }
}

void vulnerable_printf(char *input) {
    printf("Secret value address: %p\n", (void*)&secret_value);
    printf("Auth flag address: %p\n", (void*)&auth_flag);
    printf("Input buffer at: %p\n", (void*)input);
    
    printf("\n--- User input ---\n");
    // VULNERABILITY: User input directly as format string
    printf(input);
    printf("\n--- End of input ---\n");
}

int main(int argc, char *argv[]) {
    printf("=== Format String Vulnerability Practice ===\n");
    
    if (argc < 2) {
        printf("\nUsage: %s <format_string>\n", argv[0]);
        printf("\nPractice objectives:\n");
        printf("1. Read values from stack using %%x or %%p\n");
        printf("2. Read arbitrary memory using %%s\n");
        printf("3. Write to memory using %%n\n");
        printf("4. Modify auth_flag to 1337 to gain access\n");
        printf("\nHints:\n");
        printf("- Try: ./format_vuln \"%%x.%%x.%%x.%%x\"\n");
        printf("- Try: ./format_vuln \"%%p.%%p.%%p.%%p\"\n");
        return 1;
    }
    
    vulnerable_printf(argv[1]);
    
    printf("\nChecking authentication...\n");
    check_auth();
    
    return 0;
}
