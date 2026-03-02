#include <stdio.h>
#include <stdlib.h>

// Constructor function - executed when library is loaded
__attribute__((constructor))
void injected_constructor() {
    printf("[INJECTED] Constructor executed!\n");
    // Add your injection code here
}

// Destructor function - executed when library is unloaded
__attribute__((destructor))
void injected_destructor() {
    printf("[INJECTED] Destructor executed!\n");
    // Add cleanup code here
}

// Example function that can be called from injected code
void injected_function() {
    printf("[INJECTED] Custom function called!\n");
}
