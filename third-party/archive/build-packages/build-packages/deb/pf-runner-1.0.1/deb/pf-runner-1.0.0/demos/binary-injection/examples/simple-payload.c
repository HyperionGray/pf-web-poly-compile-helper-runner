#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <dlfcn.h>
#include <stdarg.h>

// Constructor function - executed when library is loaded
__attribute__((constructor))
void injected_constructor() {
    printf("[INJECTED] Simple payload constructor executed!\n");
    printf("[INJECTED] Process PID: %d\n", getpid());
    printf("[INJECTED] Injection successful!\n");
}

// Destructor function - executed when library is unloaded
__attribute__((destructor))
void injected_destructor() {
    printf("[INJECTED] Simple payload destructor executed!\n");
}

// Example function that can be called from injected code
void injected_function() {
    printf("[INJECTED] Custom function called from simple payload!\n");
}