# Heap Spray Helpers and Demonstration

This module provides comprehensive tools, examples, and documentation for understanding heap spray techniques used in memory exploitation. It's designed for security researchers, exploit developers, and defenders who need to understand these techniques.

**FOR EDUCATIONAL PURPOSES ONLY**

## Table of Contents

1. [Overview](#overview)
2. [What is Heap Spraying?](#what-is-heap-spraying)
3. [Why is Heap Spraying So Common?](#why-is-heap-spraying-so-common)
4. [Quick Start](#quick-start)
5. [Components](#components)
6. [Examples](#examples)
7. [Platform Support](#platform-support)
8. [Building](#building)
9. [Running the Demos](#running-the-demos)
10. [Understanding the Techniques](#understanding-the-techniques)
11. [Defense Mechanisms](#defense-mechanisms)
12. [References](#references)

## Overview

Heap spraying is one of the most common techniques in modern exploitation. This module helps you understand:

- **What** heap spraying is and how it works
- **Why** it's so effective and commonly used
- **How** to detect and defend against it
- **When** it's applicable in exploitation scenarios

The module includes:
- ✅ Heap spray helper library in C
- ✅ Multiple demonstration programs
- ✅ Analysis tools for detecting sprays
- ✅ Educational documentation
- ✅ Platform-specific considerations (Linux/macOS)

## What is Heap Spraying?

**Heap spraying** is a technique where an attacker allocates many chunks of memory on the heap, filling them with attacker-controlled data. This creates a predictable memory layout that makes exploitation easier.

### Key Concepts

```
Normal Heap State:          After Heap Spray:
┌─────────────┐            ┌─────────────┐
│  Code       │            │  Code       │
├─────────────┤            ├─────────────┤
│  Stack      │            │  Stack      │
├─────────────┤            ├─────────────┤
│  Heap       │            │  Heap       │
│  [random]   │    →       │  [AAAAAA]   │ ← Attacker-controlled
│  [random]   │            │  [AAAAAA]   │ ← Attacker-controlled
│  [random]   │            │  [AAAAAA]   │ ← Attacker-controlled
│  [random]   │            │  [AAAAAA]   │ ← Attacker-controlled
└─────────────┘            └─────────────┘
```

### Basic Example

```c
// Spray the heap with NOPs and shellcode
for (int i = 0; i < 1000; i++) {
    void *chunk = malloc(4096);
    memset(chunk, 0x90, 4096);  // NOP sled
    // ... place shellcode ...
}
```

## Why is Heap Spraying So Common?

Heap spraying has become ubiquitous in exploitation for several key reasons:

### 1. **Defeats ASLR (Address Space Layout Randomization)**

ASLR randomizes memory addresses to make exploitation harder. Heap spraying counters this by filling large portions of the address space with attacker-controlled data.

```
With ASLR:                  With ASLR + Heap Spray:
Random addresses            Predictable landing zones
↓                          ↓
0x7f1234000000 [?]         0x7f1234000000 [NOP NOP NOP]
0x7f1235000000 [?]         0x7f1235000000 [NOP NOP NOP]
0x7f1236000000 [?]         0x7f1236000000 [NOP NOP NOP]
                           ↑ Attacker wins regardless
```

### 2. **Makes Exploits Reliable**

Without spraying, exploits might only work once in 256 tries due to randomization. With spraying, success rates approach 90%+ because:
- Multiple landing zones exist
- Large NOP sleds provide wiggle room
- Predictable patterns emerge

### 3. **Works Across Different Heap Vulnerabilities**

Heap spraying aids exploitation of various vulnerability types:

| Vulnerability Type | How Spraying Helps |
|-------------------|-------------------|
| **Heap Overflow** | Places controlled data adjacent to vulnerable chunk |
| **Use-After-Free** | Reallocates freed memory with attacker data |
| **Double-Free** | Exploits corrupted free list with spray |
| **Metadata Corruption** | Provides fake heap structures |
| **Type Confusion** | Places objects at predictable addresses |

### 4. **Simple to Implement**

Unlike complex ROP chains or information leaks, heap spraying is straightforward:

```c
// That's it - you have a spray
for (int i = 0; i < N; i++) {
    malloc_and_fill(size, pattern);
}
```

### 5. **Platform Independent**

The core concept works across:
- Different operating systems (Linux, macOS, Windows)
- Various browsers (Chrome, Firefox, Safari)
- Multiple languages (JavaScript, C, C++, Java)
- Different allocators (glibc malloc, jemalloc, tcmalloc)

## Quick Start

### Prerequisites

- GCC or Clang compiler
- Make build system
- Linux or macOS (primary support)

### Build Everything

```bash
# From repository root
pf build-heap-spray-demos

# Or using make directly
cd demos/heap-spray
make all
```

### Run Basic Demo

```bash
# Run basic heap spray demonstration
pf demo-heap-spray-basic

# Or directly
./demos/heap-spray/build/basic_demo
```

### Run Vulnerability Demo

```bash
# See why spraying is so common
pf demo-heap-spray-vulns

# Or directly
./demos/heap-spray/build/vulnerability_demo
```

### Run Analysis Tool

```bash
# Analyze and detect heap spray patterns
pf demo-heap-spray-analyze

# Or directly
./demos/heap-spray/build/heap_analyzer
```

## Components

### 1. Heap Spray Library (`src/heap_spray.h` & `src/heap_spray.c`)

Core library providing:

```c
// Basic spray interface
heap_spray_result_t *heap_spray_basic(
    size_t chunk_size,      // Size of each allocation
    size_t num_chunks,      // Number to allocate
    const uint8_t *pattern, // Fill pattern
    size_t pattern_size     // Pattern size
);

// Advanced configuration
heap_spray_config_t config;
heap_spray_init_config(&config);
config.chunk_size = 8192;
config.num_chunks = 100;
heap_spray_result_t *result = heap_spray_execute(&config);

// Heap grooming for targeted exploitation
heap_groom_config_t groom = {
    .initial_allocs = 20,
    .hole_size = 2048,
    .num_holes = 10,
    .target_chunk_size = 2048
};
heap_spray_result_t *groomed = heap_groom_prepare(&groom);

// Cleanup
heap_spray_cleanup(result);
```

**Key Features:**
- Multiple spray patterns (NOP sleds for x86/x64/ARM)
- Heap statistics and monitoring
- Vulnerability simulation
- Platform detection
- Memory visualization

### 2. Basic Demo (`examples/basic_demo.c`)

Demonstrates fundamental heap spray concepts:
- Basic heap spraying
- Pattern-based spraying
- Heap grooming
- Statistics monitoring

**Run it:**
```bash
./demos/heap-spray/build/basic_demo
```

### 3. Vulnerability Demo (`examples/vulnerability_demo.c`)

Shows why heap spraying is essential for exploiting:
- Heap overflow vulnerabilities
- Use-after-free bugs
- Double-free issues
- Heap metadata corruption
- Complete exploitation flow

**Run it:**
```bash
./demos/heap-spray/build/vulnerability_demo
```

### 4. Analysis Tool (`tools/heap_analyzer.c`)

Detection and analysis capabilities:
- Pattern detection
- Entropy calculation
- Spray identification
- Defensive monitoring
- Real-time analysis

**Run it:**
```bash
./demos/heap-spray/build/heap_analyzer
```

## Examples

### Example 1: Basic Heap Spray

```c
#include "heap_spray.h"

int main() {
    // Spray 100 chunks of 4KB each
    heap_spray_result_t *spray = heap_spray_basic(
        4096,  // chunk size
        100,   // number of chunks
        NULL,  // default pattern
        0
    );
    
    // Print statistics
    heap_spray_print_stats(spray);
    
    // Visualize allocations
    heap_visualize_allocations(spray);
    
    // Cleanup
    heap_spray_cleanup(spray);
    return 0;
}
```

### Example 2: NOP Sled Spray

```c
#include "heap_spray.h"

int main() {
    // Create NOP sled pattern
    uint8_t nops[8];
    create_nop_sled(nops, sizeof(nops), "x86_64");
    
    // Spray heap with NOPs
    heap_spray_result_t *spray = heap_spray_basic(
        8192,          // chunk size
        200,           // number of chunks
        nops,          // NOP pattern
        sizeof(nops)
    );
    
    printf("Sprayed %zu MB with NOP sleds\n",
           spray->total_bytes / (1024 * 1024));
    
    heap_spray_cleanup(spray);
    return 0;
}
```

### Example 3: Heap Grooming

```c
#include "heap_spray.h"

int main() {
    // Prepare heap layout for exploitation
    heap_groom_config_t config = {
        .initial_allocs = 30,
        .hole_size = 1024,
        .num_holes = 15,
        .target_chunk_size = 1024
    };
    
    heap_spray_result_t *groomed = heap_groom_prepare(&config);
    
    // Heap is now prepared with predictable holes
    // Perfect for targeted exploitation
    
    heap_spray_cleanup(groomed);
    return 0;
}
```

## Platform Support

### Linux

✅ **Fully Supported**
- glibc malloc heap statistics
- `/proc/self/maps` parsing
- ASLR detection
- Complete feature set

**Specifics:**
```c
// Linux-specific heap stats
heap_stats_t stats;
heap_get_stats(&stats);  // Uses mallinfo()
```

### macOS

✅ **Supported**
- Basic functionality
- Platform detection
- Limited heap statistics

**Specifics:**
```c
// macOS detection
if (get_platform() == PLATFORM_MACOS) {
    printf("Running on macOS\n");
}
```

### Windows

⚠️ **Partial Support**
- Core spray functionality works
- Statistics may be limited
- Requires platform-specific compilation

## Building

### Using pf Tasks

```bash
# Build all heap spray demos
pf build-heap-spray-demos

# Build specific component
pf build-heap-spray-lib      # Library only
pf build-heap-spray-basic    # Basic demo
pf build-heap-spray-vulns    # Vulnerability demo
pf build-heap-spray-tools    # Analysis tools
```

### Using Make

```bash
cd demos/heap-spray

# Build everything
make all

# Build specific targets
make basic_demo
make vulnerability_demo
make heap_analyzer

# Clean
make clean
```

### Manual Compilation

```bash
# Compile library
gcc -c -O2 src/heap_spray.c -o heap_spray.o

# Link with demo
gcc basic_demo.c heap_spray.o -o basic_demo -lm
```

## Running the Demos

### 1. Basic Demo

```bash
pf demo-heap-spray-basic
```

**What it shows:**
- Fundamental heap spray mechanics
- Memory address patterns
- Allocation visualization
- Statistics tracking

**Expected output:**
```
===== BASIC HEAP SPRAY DEMONSTRATION =====

Platform: Linux
Architecture: x86_64

[*] Performing basic heap spray with 50 chunks of 4KB each...
[+] Heap spray completed!
[+] Successfully allocated 50 chunks (204800 bytes total)
[+] Address range: 0x5555557d7000 - 0x5555558f2000

=== Heap Spray Statistics ===
Number of allocations: 50
Total bytes allocated: 204800 (0.20 MB)
...
```

### 2. Vulnerability Demo

```bash
pf demo-heap-spray-vulns
```

**What it shows:**
- Heap overflow scenarios
- Use-after-free exploitation
- Double-free vulnerabilities
- Why spraying makes exploitation easier

**Expected output:**
```
===== HEAP OVERFLOW VULNERABILITY =====

Heap overflow occurs when data is written beyond boundaries...

[*] Creating vulnerable scenario...
Chunk 1 at: 0x555555559260
Chunk 2 at: 0x555555559290

WHY HEAP SPRAY HELPS:
By spraying the heap with controlled data, an attacker can:
1. Predict where data will land after overflow
2. Ensure overflow hits attacker-controlled memory
3. Place shellcode/gadgets at predictable addresses
...
```

### 3. Analysis Tool

```bash
pf demo-heap-spray-analyze
```

**What it shows:**
- Pattern detection techniques
- Entropy analysis
- Spray identification
- Defensive monitoring

**Expected output:**
```
╔═══════════════════════════════════════════════════╗
║           HEAP SPRAY DETECTION ANALYSIS           ║
╚═══════════════════════════════════════════════════╝

Number of allocations: 30
Total size: 122880 bytes (0.12 MB)
Pattern repetition score: 98.00%

⚠️  HIGH CONFIDENCE: Heap spray pattern detected!

Indicators:
  ✓ Many similar allocations (30)
  ✓ High pattern repetition (98%)
...
```

## Understanding the Techniques

### Technique 1: Basic Heap Spray

**Goal:** Fill heap with attacker-controlled data

**Method:**
1. Allocate many chunks
2. Fill with predictable pattern
3. Trigger vulnerability
4. Control flow lands in spray

**Effectiveness:** ⭐⭐⭐⭐⭐

### Technique 2: Heap Grooming

**Goal:** Create specific memory layout

**Method:**
1. Allocate initial chunks
2. Free specific ones to create holes
3. Spray to fill holes
4. Exploit uses groomed layout

**Effectiveness:** ⭐⭐⭐⭐

### Technique 3: Feng Shui

**Goal:** Precise heap layout control

**Method:**
1. Carefully allocate/free in specific order
2. Create predictable adjacency
3. Place vulnerable object
4. Overflow into controlled data

**Effectiveness:** ⭐⭐⭐⭐⭐

### Technique 4: Type Confusion

**Goal:** Replace object with attacker-controlled fake

**Method:**
1. Free object A
2. Spray with fake objects
3. Use-after-free references fake object
4. Control virtual table or function pointers

**Effectiveness:** ⭐⭐⭐⭐

## Defense Mechanisms

### Active Defenses

| Defense | Description | Effectiveness |
|---------|-------------|---------------|
| **ASLR** | Randomize memory layout | ⭐⭐⭐ (weakened by spray) |
| **Heap Canaries** | Detect metadata corruption | ⭐⭐⭐⭐ |
| **Safe Unlinking** | Validate heap pointers | ⭐⭐⭐⭐ |
| **Hardened Allocators** | tcmalloc, jemalloc | ⭐⭐⭐⭐ |
| **Memory Tagging** | ARM MTE, Intel LVI | ⭐⭐⭐⭐⭐ |

### Detection Strategies

```c
// Monitor allocation patterns
bool detect_spray(allocator_stats_t *stats) {
    return (stats->recent_alloc_count > THRESHOLD) &&
           (stats->avg_chunk_size_variance < VARIANCE_THRESHOLD);
}

// Check for repetitive patterns
bool check_pattern(void *chunk, size_t size) {
    double entropy = calculate_entropy(chunk, size);
    return entropy < LOW_ENTROPY_THRESHOLD;
}

// Rate limiting
bool should_block(alloc_request_t *req) {
    return req->allocs_per_second > RATE_LIMIT;
}
```

### Mitigation in Code

```c
// Limit allocation size
void *safe_malloc(size_t size) {
    if (size > MAX_ALLOC_SIZE) {
        log_suspicious("Large allocation blocked");
        return NULL;
    }
    return malloc(size);
}

// Rate limit allocations
void *rate_limited_malloc(size_t size) {
    static time_t last_reset = 0;
    static int alloc_count = 0;
    
    time_t now = time(NULL);
    if (now - last_reset > 1) {
        alloc_count = 0;
        last_reset = now;
    }
    
    if (++alloc_count > MAX_ALLOCS_PER_SECOND) {
        log_suspicious("Allocation rate limit exceeded");
        return NULL;
    }
    
    return malloc(size);
}
```

## References

### Academic Papers

1. **"Heap Feng Shui in JavaScript"** - Alexander Sotirov (Black Hat Europe 2007)
   - First systematic study of heap manipulation in browsers

2. **"Understanding and Preventing Heap Exploitation"** - Multiple Authors
   - Comprehensive overview of heap vulnerabilities

3. **"The Geometry of Innocent Flesh on the Bone"** - Tyler Durden (Phrack)
   - Classic heap exploitation techniques

### Practical Resources

- [Azeria Labs - Heap Exploitation](https://azeria-labs.com/heap-exploitation-part-1/)
- [Shellphish - How2Heap](https://github.com/shellphish/how2heap)
- [LiveOverflow - Heap Exploitation Series](https://www.youtube.com/c/LiveOverflow)

### Security Advisories

Many real-world exploits use heap spraying:
- CVE-2012-0507 (Java)
- CVE-2013-0431 (Java)
- CVE-2014-1776 (Internet Explorer)
- CVE-2016-0189 (Internet Explorer)

## License

FOR EDUCATIONAL PURPOSES ONLY

This code is provided for security research and education. Use responsibly and legally.

## Contributing

Contributions welcome! Please:
1. Add tests for new features
2. Document exploitation techniques
3. Include educational explanations
4. Follow existing code style

## Support

- Open issues for bugs or questions
- Check existing demos for examples
- Review the inline code documentation

---

**Remember:** These techniques are powerful. Use them ethically and legally, only on systems you own or have explicit permission to test.
