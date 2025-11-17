// C example - vulnerable buffer overflow for debugging practice
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void vulnerable_function(char *input) {
    char buffer[64];
    printf("Buffer address: %p\n", buffer);
    strcpy(buffer, input);  // Vulnerable: no bounds checking
    printf("You entered: %s\n", buffer);
}

void secret_function() {
    printf("\n🎉 Secret function reached! 🎉\n");
    printf("This function should only be called through exploitation.\n");
}

int calculate_sum(int a, int b) {
    int result = a + b;
    return result;
}

void print_info(const char *name, int age) {
    printf("Name: %s, Age: %d\n", name, age);
}

int main(int argc, char *argv[]) {
    printf("=== Debug Practice Program (C) ===\n");
    printf("Secret function address: %p\n", secret_function);
    
    if (argc < 2) {
        printf("Usage: %s <input_string>\n", argv[0]);
        printf("Try debugging to explore the vulnerability!\n");
        return 1;
    }
    
    int x = 10, y = 20;
    int sum = calculate_sum(x, y);
    printf("Sum of %d and %d = %d\n", x, y, sum);
    
    print_info("Alice", 25);
    
    printf("\nCalling vulnerable function...\n");
    vulnerable_function(argv[1]);
    
    printf("Program finished normally.\n");
    return 0;
}
