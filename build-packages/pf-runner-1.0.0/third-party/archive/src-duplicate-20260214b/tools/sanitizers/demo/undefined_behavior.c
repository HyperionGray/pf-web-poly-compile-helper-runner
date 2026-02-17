#include <limits.h>
#include <stdio.h>

int main(void) {
  // Intentional signed overflow (undefined behavior).
  int x = INT_MAX;
  int y = x + 1;
  printf("%d\n", y);
  return 0;
}

