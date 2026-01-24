#include <stdio.h>

// Minimal C stand-in for the original Fortran hello.f90 so we can
// produce a WASM artifact without needing wasm-capable lfortran.
int main(void) {
    puts("Hello from Fortran (stub via C)!");
    return 0;
}
