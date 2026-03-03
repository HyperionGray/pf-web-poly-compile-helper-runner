#include <stdio.h>

// Forward declaration of Fortran subroutine
extern void injected_fortran_constructor(void);

// C constructor that calls Fortran code
__attribute__((constructor))
void fortran_injection_constructor() {
    printf("[INJECTED] C wrapper calling Fortran constructor...\n");
    injected_fortran_constructor();
}

// C destructor
__attribute__((destructor))
void fortran_injection_destructor() {
    printf("[INJECTED] Fortran injection destructor executed!\n");
}