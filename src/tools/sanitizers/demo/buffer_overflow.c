#include <stdio.h>
#include <string.h>

int main(void) {
  char buf[8];
  // Intentional overflow for sanitizer demo.
  const char *src = "AAAAAAAAAAAAAAAA";
  memcpy(buf, src, strlen(src) + 1);
  puts(buf);
  return 0;
}

