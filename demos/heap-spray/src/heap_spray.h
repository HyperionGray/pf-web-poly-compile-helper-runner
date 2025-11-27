/**
 * Heap Spray Helper Library
 * 
 * This library provides utilities for understanding and demonstrating
 * heap spray techniques commonly used in memory exploitation.
 * 
 * FOR EDUCATIONAL PURPOSES ONLY
 */

#ifndef HEAP_SPRAY_H
#define HEAP_SPRAY_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

// Heap spray configuration
typedef struct {
    size_t chunk_size;        // Size of each heap chunk to spray
    size_t num_chunks;        // Number of chunks to allocate
    uint8_t *pattern;         // Pattern to fill chunks with
    size_t pattern_size;      // Size of the pattern
    bool random_sizes;        // Use random chunk sizes
    size_t min_size;          // Minimum chunk size (if random)
    size_t max_size;          // Maximum chunk size (if random)
} heap_spray_config_t;

// Heap spray result tracking
typedef struct {
    void **allocations;       // Array of allocated pointers
    size_t num_allocations;   // Number of successful allocations
    size_t total_bytes;       // Total bytes allocated
    uintptr_t min_addr;       // Minimum address allocated
    uintptr_t max_addr;       // Maximum address allocated
} heap_spray_result_t;

// Common heap spray patterns
extern const uint8_t NOP_SLED_X86[];
extern const size_t NOP_SLED_X86_SIZE;

extern const uint8_t NOP_SLED_X86_64[];
extern const size_t NOP_SLED_X86_64_SIZE;

extern const uint8_t NOP_SLED_ARM[];
extern const size_t NOP_SLED_ARM_SIZE;

// Initialize spray configuration with defaults
void heap_spray_init_config(heap_spray_config_t *config);

// Perform heap spray with given configuration
heap_spray_result_t *heap_spray_execute(const heap_spray_config_t *config);

// Perform basic heap spray (simpler interface)
heap_spray_result_t *heap_spray_basic(size_t chunk_size, size_t num_chunks, 
                                      const uint8_t *pattern, size_t pattern_size);

// Clean up heap spray allocations
void heap_spray_cleanup(heap_spray_result_t *result);

// Print heap spray statistics
void heap_spray_print_stats(const heap_spray_result_t *result);

// Heap analysis utilities
typedef struct {
    size_t total_allocations;
    size_t total_free_chunks;
    size_t largest_free_chunk;
    size_t total_allocated_bytes;
    size_t heap_fragmentation_pct;
} heap_stats_t;

// Get current heap statistics (platform-dependent)
bool heap_get_stats(heap_stats_t *stats);

// Print heap statistics
void heap_print_stats(const heap_stats_t *stats);

// Heap inspection utilities
void heap_dump_region(void *addr, size_t size);
bool heap_check_pattern(void *addr, const uint8_t *pattern, size_t pattern_size);
void heap_visualize_allocations(const heap_spray_result_t *result);

// Heap grooming utilities (prepare heap for exploitation)
typedef struct {
    size_t initial_allocs;    // Initial allocations to fragment heap
    size_t hole_size;         // Size of holes to create
    size_t num_holes;         // Number of holes to create
    size_t target_chunk_size; // Target size for exploitation
} heap_groom_config_t;

heap_spray_result_t *heap_groom_prepare(const heap_groom_config_t *config);

// Create predictable heap layout (for educational purposes)
void *heap_groom_create_target(size_t size);

// Exploit simulation structures (for demonstration)
typedef enum {
    HEAP_OVERFLOW,
    USE_AFTER_FREE,
    DOUBLE_FREE,
    HEAP_METADATA_CORRUPTION,
    UNLINK_EXPLOIT
} heap_vuln_type_t;

typedef struct {
    heap_vuln_type_t type;
    void *vulnerable_chunk;
    void *overflow_source;
    size_t overflow_size;
    bool triggered;
} heap_vuln_sim_t;

// Simulate heap vulnerabilities (for educational demonstration)
heap_vuln_sim_t *heap_vuln_simulate(heap_vuln_type_t type, size_t chunk_size);

// Demonstrate vulnerability without actually exploiting
void heap_vuln_demonstrate(const heap_vuln_sim_t *vuln);

// Clean up vulnerability simulation
void heap_vuln_cleanup(heap_vuln_sim_t *vuln);

// Helper functions for creating common patterns
void create_nop_sled(uint8_t *buffer, size_t size, const char *arch);
void create_shellcode_pattern(uint8_t *buffer, size_t size);
void create_return_address_pattern(uint8_t *buffer, size_t size, uintptr_t target_addr);

// Platform detection
typedef enum {
    PLATFORM_LINUX,
    PLATFORM_MACOS,
    PLATFORM_WINDOWS,
    PLATFORM_UNKNOWN
} platform_t;

platform_t get_platform(void);
const char *get_platform_name(void);

// Architecture detection
typedef enum {
    ARCH_X86,
    ARCH_X86_64,
    ARCH_ARM,
    ARCH_ARM64,
    ARCH_UNKNOWN
} arch_t;

arch_t get_arch(void);
const char *get_arch_name(void);

#endif /* HEAP_SPRAY_H */
