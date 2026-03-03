#include <stdio.h>
#include <stdlib.h>
int main() {
    void* p = malloc(100);
    printf("Allocated: %p\\n", p);
    free(p);
    return 0;
}
