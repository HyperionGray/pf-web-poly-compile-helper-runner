#include <emscripten.h>

EMSCRIPTEN_KEEPALIVE
int trigger_trap() {
    __builtin_trap();
    return 0;
}

EMSCRIPTEN_KEEPALIVE
int main() {
    return 42;
}
