# Fuzzing Examples

This directory contains example programs for demonstrating fuzzing capabilities.

## vulnerable.c

A deliberately vulnerable program with multiple bug classes:
- Buffer overflow
- Null pointer dereference
- Heap overflow

### Build for libfuzzer:
```bash
pf build-libfuzzer-target source=demos/fuzzing/examples/vulnerable.c output=demos/fuzzing/examples/fuzzer
```

### Build for AFL++:
```bash
pf build-afl-target source=demos/fuzzing/examples/vulnerable.c output=demos/fuzzing/examples/vulnerable_afl
```

### Run libfuzzer:
```bash
pf run-libfuzzer target=demos/fuzzing/examples/fuzzer corpus=demos/fuzzing/corpus time=60
```

### Run AFL++:
```bash
pf afl-fuzz target=demos/fuzzing/examples/vulnerable_afl input=demos/fuzzing/in output=demos/fuzzing/out
```
