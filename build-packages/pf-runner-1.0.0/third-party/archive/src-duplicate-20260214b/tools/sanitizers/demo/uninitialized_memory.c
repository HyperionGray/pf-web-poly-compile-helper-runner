#include <stdio.h>

int main(void) {
  volatile int x;
  // Intentional use of uninitialized variable for sanitizer demo.
  if (x == 42) {
    puts("unreachable");
  }
  return x;
}

