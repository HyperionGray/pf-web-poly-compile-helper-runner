// Heap-based buffer overflow practice binary
// Purpose: Learn heap exploitation techniques
// Vulnerability: Heap buffer overflow allowing metadata corruption

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef struct {
    char name[32];
    void (*print_func)();
} User;

void normal_print() {
    printf("Normal user function called.\n");
}

void admin_print() {
    printf("\n🔓 ADMIN ACCESS GRANTED! 🔓\n");
    printf("This demonstrates heap exploitation success.\n");
    system("/bin/sh");
}

void create_user(char *username) {
    User *user = (User*)malloc(sizeof(User));
    if (!user) {
        printf("Memory allocation failed!\n");
        return;
    }
    
    printf("Allocated User struct at: %p\n", (void*)user);
    printf("Function pointer is at: %p\n", (void*)&user->print_func);
    printf("Admin function is at: %p\n", (void*)admin_print);
    
    user->print_func = normal_print;
    
    // VULNERABILITY: No bounds checking on strcpy
    strcpy(user->name, username);
    
    printf("User name: %s\n", user->name);
    printf("Calling user function...\n");
    user->print_func();
    
    free(user);
}

int main(int argc, char *argv[]) {
    printf("=== Heap Buffer Overflow Practice ===\n");
    
    if (argc < 2) {
        printf("\nUsage: %s <username>\n", argv[0]);
        printf("\nPractice objectives:\n");
        printf("1. Understand heap memory layout\n");
        printf("2. Identify offset to function pointer\n");
        printf("3. Craft payload to overwrite function pointer\n");
        printf("4. Redirect execution to admin_print()\n");
        return 1;
    }
    
    create_user(argv[1]);
    
    printf("\nProgram completed.\n");
    return 0;
}
