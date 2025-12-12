/**
 * Heap Spray Helper Library Implementation
 * 
 * FOR EDUCATIONAL PURPOSES ONLY
 */

#include "heap_spray.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#ifdef __linux__
#include <malloc.h>
#endif

// NOP sled patterns for different architectures
const uint8_t NOP_SLED_X86[] = {0x90, 0x90, 0x90, 0x90};
const size_t NOP_SLED_X86_SIZE = sizeof(NOP_SLED_X86);

const uint8_t NOP_SLED_X86_64[] = {0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90};
const size_t NOP_SLED_X86_64_SIZE = sizeof(NOP_SLED_X86_64);

const uint8_t NOP_SLED_ARM[] = {0x00, 0xF0, 0x20, 0xE3}; // NOP in ARM
const size_t NOP_SLED_ARM_SIZE = sizeof(NOP_SLED_ARM);

// Initialize spray configuration with defaults
void heap_spray_init_config(heap_spray_config_t *config) {
    if (!config) return;
    
    config->chunk_size = 4096;
    config->num_chunks = 100;
    config->pattern = NULL;
    config->pattern_size = 0;
    config->random_sizes = false;
    config->min_size = 1024;
    config->max_size = 8192;
}

// Perform heap spray with given configuration
heap_spray_result_t *heap_spray_execute(const heap_spray_config_t *config) {
    if (!config || config->num_chunks == 0) return NULL;
    
    heap_spray_result_t *result = calloc(1, sizeof(heap_spray_result_t));
    if (!result) return NULL;
    
    result->allocations = calloc(config->num_chunks, sizeof(void *));
    if (!result->allocations) {
        free(result);
        return NULL;
    }
    
    result->min_addr = UINTPTR_MAX;
    result->max_addr = 0;
    
    // Seed random number generator for random sizes
    if (config->random_sizes) {
        srand(time(NULL));
    }
    
    printf("[*] Starting heap spray...\n");
    printf("[*] Configuration:\n");
    printf("    - Chunk size: %zu bytes\n", config->chunk_size);
    printf("    - Number of chunks: %zu\n", config->num_chunks);
    printf("    - Random sizes: %s\n", config->random_sizes ? "yes" : "no");
    
    for (size_t i = 0; i < config->num_chunks; i++) {
        size_t alloc_size = config->chunk_size;
        
        if (config->random_sizes) {
            alloc_size = config->min_size + 
                        (rand() % (config->max_size - config->min_size + 1));
        }
        
        void *chunk = malloc(alloc_size);
        if (!chunk) {
            printf("[!] Allocation failed at chunk %zu\n", i);
            continue;
        }
        
        // Fill with pattern if provided
        if (config->pattern && config->pattern_size > 0) {
            for (size_t offset = 0; offset < alloc_size; offset += config->pattern_size) {
                size_t copy_size = config->pattern_size;
                if (offset + copy_size > alloc_size) {
                    copy_size = alloc_size - offset;
                }
                memcpy((uint8_t *)chunk + offset, config->pattern, copy_size);
            }
        } else {
            // Fill with 0x41 ('A') as default pattern
            memset(chunk, 0x41, alloc_size);
        }
        
        result->allocations[result->num_allocations++] = chunk;
        result->total_bytes += alloc_size;
        
        uintptr_t addr = (uintptr_t)chunk;
        if (addr < result->min_addr) result->min_addr = addr;
        if (addr > result->max_addr) result->max_addr = addr;
    }
    
    printf("[+] Heap spray completed!\n");
    printf("[+] Successfully allocated %zu chunks (%zu bytes total)\n", 
           result->num_allocations, result->total_bytes);
    printf("[+] Address range: 0x%lx - 0x%lx\n", 
           (unsigned long)result->min_addr, (unsigned long)result->max_addr);
    
    return result;
}

// Perform basic heap spray (simpler interface)
heap_spray_result_t *heap_spray_basic(size_t chunk_size, size_t num_chunks, 
                                      const uint8_t *pattern, size_t pattern_size) {
    heap_spray_config_t config;
    heap_spray_init_config(&config);
    
    config.chunk_size = chunk_size;
    config.num_chunks = num_chunks;
    config.pattern = (uint8_t *)pattern;
    config.pattern_size = pattern_size;
    
    return heap_spray_execute(&config);
}

// Clean up heap spray allocations
void heap_spray_cleanup(heap_spray_result_t *result) {
    if (!result) return;
    
    if (result->allocations) {
        for (size_t i = 0; i < result->num_allocations; i++) {
            free(result->allocations[i]);
        }
        free(result->allocations);
    }
    
    free(result);
}

// Print heap spray statistics
void heap_spray_print_stats(const heap_spray_result_t *result) {
    if (!result) return;
    
    printf("\n=== Heap Spray Statistics ===\n");
    printf("Number of allocations: %zu\n", result->num_allocations);
    printf("Total bytes allocated: %zu (%.2f MB)\n", 
           result->total_bytes, result->total_bytes / (1024.0 * 1024.0));
    printf("Address range: 0x%lx - 0x%lx\n", 
           (unsigned long)result->min_addr, (unsigned long)result->max_addr);
    printf("Range size: %zu bytes (%.2f MB)\n",
           (size_t)(result->max_addr - result->min_addr),
           (result->max_addr - result->min_addr) / (1024.0 * 1024.0));
    printf("===========================\n\n");
}

// Get current heap statistics
bool heap_get_stats(heap_stats_t *stats) {
    if (!stats) return false;
    
    memset(stats, 0, sizeof(heap_stats_t));
    
#ifdef __linux__
    struct mallinfo mi = mallinfo();
    stats->total_allocations = mi.hblks;
    stats->total_allocated_bytes = mi.uordblks;
    stats->largest_free_chunk = mi.fordblks;
    
    if (mi.arena > 0) {
        stats->heap_fragmentation_pct = 
            (mi.fordblks * 100) / mi.arena;
    }
    
    return true;
#else
    // Platform-specific implementations would go here
    return false;
#endif
}

// Print heap statistics
void heap_print_stats(const heap_stats_t *stats) {
    if (!stats) return;
    
    printf("\n=== Current Heap Statistics ===\n");
    printf("Total allocated bytes: %zu\n", stats->total_allocated_bytes);
    printf("Largest free chunk: %zu\n", stats->largest_free_chunk);
    printf("Heap fragmentation: %zu%%\n", stats->heap_fragmentation_pct);
    printf("==============================\n\n");
}

// Dump heap region
void heap_dump_region(void *addr, size_t size) {
    if (!addr || size == 0) return;
    
    printf("\n=== Heap Dump at 0x%lx (%zu bytes) ===\n", 
           (unsigned long)addr, size);
    
    uint8_t *ptr = (uint8_t *)addr;
    for (size_t i = 0; i < size && i < 256; i += 16) {
        printf("0x%08lx: ", (unsigned long)(ptr + i));
        
        // Hex dump
        for (size_t j = 0; j < 16 && (i + j) < size; j++) {
            printf("%02x ", ptr[i + j]);
        }
        
        // ASCII dump
        printf(" |");
        for (size_t j = 0; j < 16 && (i + j) < size; j++) {
            uint8_t c = ptr[i + j];
            printf("%c", (c >= 32 && c < 127) ? c : '.');
        }
        printf("|\n");
    }
    
    printf("=====================================\n\n");
}

// Check if pattern exists at address
bool heap_check_pattern(void *addr, const uint8_t *pattern, size_t pattern_size) {
    if (!addr || !pattern || pattern_size == 0) return false;
    return memcmp(addr, pattern, pattern_size) == 0;
}

// Visualize heap allocations
void heap_visualize_allocations(const heap_spray_result_t *result) {
    if (!result || !result->allocations) return;
    
    printf("\n=== Heap Allocation Visualization ===\n");
    printf("Each '█' represents an allocation:\n\n");
    
    for (size_t i = 0; i < result->num_allocations && i < 100; i++) {
        printf("█");
        if ((i + 1) % 50 == 0) printf("\n");
    }
    
    if (result->num_allocations > 100) {
        printf("\n... and %zu more allocations\n", result->num_allocations - 100);
    }
    
    printf("\n\n=====================================\n\n");
}

// Heap grooming - prepare heap for exploitation
heap_spray_result_t *heap_groom_prepare(const heap_groom_config_t *config) {
    if (!config) return NULL;
    
    printf("[*] Starting heap grooming...\n");
    
    // Allocate initial chunks to fragment heap
    void **initial_allocs = calloc(config->initial_allocs, sizeof(void *));
    if (!initial_allocs) return NULL;
    
    for (size_t i = 0; i < config->initial_allocs; i++) {
        initial_allocs[i] = malloc(config->hole_size);
    }
    
    // Free every other allocation to create holes
    for (size_t i = 0; i < config->initial_allocs; i += 2) {
        free(initial_allocs[i]);
        initial_allocs[i] = NULL;
    }
    
    printf("[+] Created %zu holes of size %zu\n", 
           config->num_holes, config->hole_size);
    
    // Now spray with target-sized chunks
    heap_spray_result_t *result = heap_spray_basic(
        config->target_chunk_size, config->num_holes, NULL, 0);
    
    // Clean up remaining initial allocations
    for (size_t i = 0; i < config->initial_allocs; i++) {
        if (initial_allocs[i]) free(initial_allocs[i]);
    }
    free(initial_allocs);
    
    return result;
}

// Create predictable heap layout
void *heap_groom_create_target(size_t size) {
    void *target = malloc(size);
    if (target) {
        memset(target, 0x42, size);
        printf("[+] Created target allocation at 0x%lx\n", (unsigned long)target);
    }
    return target;
}

// Simulate heap vulnerability
heap_vuln_sim_t *heap_vuln_simulate(heap_vuln_type_t type, size_t chunk_size) {
    heap_vuln_sim_t *vuln = calloc(1, sizeof(heap_vuln_sim_t));
    if (!vuln) return NULL;
    
    vuln->type = type;
    vuln->vulnerable_chunk = malloc(chunk_size);
    vuln->triggered = false;
    
    if (!vuln->vulnerable_chunk) {
        free(vuln);
        return NULL;
    }
    
    memset(vuln->vulnerable_chunk, 0x43, chunk_size);
    
    switch (type) {
        case HEAP_OVERFLOW:
            printf("[*] Simulating heap overflow vulnerability\n");
            vuln->overflow_source = malloc(chunk_size * 2);
            vuln->overflow_size = chunk_size * 2;
            memset(vuln->overflow_source, 0x44, chunk_size * 2);
            break;
            
        case USE_AFTER_FREE:
            printf("[*] Simulating use-after-free vulnerability\n");
            break;
            
        case DOUBLE_FREE:
            printf("[*] Simulating double-free vulnerability\n");
            break;
            
        case HEAP_METADATA_CORRUPTION:
            printf("[*] Simulating heap metadata corruption\n");
            break;
            
        case UNLINK_EXPLOIT:
            printf("[*] Simulating unlink exploit scenario\n");
            break;
    }
    
    return vuln;
}

// Demonstrate vulnerability
void heap_vuln_demonstrate(const heap_vuln_sim_t *vuln) {
    if (!vuln) return;
    
    printf("\n=== Vulnerability Demonstration ===\n");
    
    switch (vuln->type) {
        case HEAP_OVERFLOW:
            printf("Type: Heap Overflow\n");
            printf("Vulnerable chunk: 0x%lx\n", (unsigned long)vuln->vulnerable_chunk);
            printf("This vulnerability allows writing beyond allocated chunk boundaries\n");
            printf("Common causes: strcpy, memcpy without bounds checking\n");
            break;
            
        case USE_AFTER_FREE:
            printf("Type: Use-After-Free\n");
            printf("Vulnerable chunk: 0x%lx\n", (unsigned long)vuln->vulnerable_chunk);
            printf("This vulnerability occurs when memory is used after being freed\n");
            printf("Common causes: dangling pointers, race conditions\n");
            break;
            
        case DOUBLE_FREE:
            printf("Type: Double-Free\n");
            printf("Vulnerable chunk: 0x%lx\n", (unsigned long)vuln->vulnerable_chunk);
            printf("This vulnerability occurs when memory is freed multiple times\n");
            printf("Common causes: error handling bugs, complex cleanup logic\n");
            break;
            
        case HEAP_METADATA_CORRUPTION:
            printf("Type: Heap Metadata Corruption\n");
            printf("Vulnerable chunk: 0x%lx\n", (unsigned long)vuln->vulnerable_chunk);
            printf("This vulnerability corrupts heap allocator metadata\n");
            printf("Common causes: buffer overflows into chunk headers\n");
            break;
            
        case UNLINK_EXPLOIT:
            printf("Type: Unlink Exploit\n");
            printf("Vulnerable chunk: 0x%lx\n", (unsigned long)vuln->vulnerable_chunk);
            printf("This vulnerability exploits heap coalescing mechanisms\n");
            printf("Common causes: corrupted forward/backward pointers\n");
            break;
    }
    
    printf("==================================\n\n");
}

// Clean up vulnerability simulation
void heap_vuln_cleanup(heap_vuln_sim_t *vuln) {
    if (!vuln) return;
    
    if (vuln->vulnerable_chunk) free(vuln->vulnerable_chunk);
    if (vuln->overflow_source) free(vuln->overflow_source);
    free(vuln);
}

// Create NOP sled for given architecture
void create_nop_sled(uint8_t *buffer, size_t size, const char *arch) {
    if (!buffer || !arch || size == 0) return;
    
    const uint8_t *pattern = NOP_SLED_X86_64;
    size_t pattern_size = NOP_SLED_X86_64_SIZE;
    
    if (strcmp(arch, "x86") == 0) {
        pattern = NOP_SLED_X86;
        pattern_size = NOP_SLED_X86_SIZE;
    } else if (strcmp(arch, "arm") == 0) {
        pattern = NOP_SLED_ARM;
        pattern_size = NOP_SLED_ARM_SIZE;
    }
    
    for (size_t i = 0; i < size; i += pattern_size) {
        size_t copy_size = pattern_size;
        if (i + copy_size > size) copy_size = size - i;
        memcpy(buffer + i, pattern, copy_size);
    }
}

// Create shellcode pattern (placeholder)
void create_shellcode_pattern(uint8_t *buffer, size_t size) {
    if (!buffer || size == 0) return;
    
    // This is just a pattern, not real shellcode
    const uint8_t pattern[] = {0xCC, 0xCC, 0xCC, 0xCC}; // INT3 breakpoints
    
    for (size_t i = 0; i < size; i += sizeof(pattern)) {
        size_t copy_size = sizeof(pattern);
        if (i + copy_size > size) copy_size = size - i;
        memcpy(buffer + i, pattern, copy_size);
    }
}

// Create return address pattern
void create_return_address_pattern(uint8_t *buffer, size_t size, uintptr_t target_addr) {
    if (!buffer || size == 0) return;
    
    size_t addr_size = sizeof(uintptr_t);
    for (size_t i = 0; i < size; i += addr_size) {
        size_t copy_size = addr_size;
        if (i + copy_size > size) copy_size = size - i;
        memcpy(buffer + i, &target_addr, copy_size);
    }
}

// Get platform
platform_t get_platform(void) {
#ifdef __linux__
    return PLATFORM_LINUX;
#elif defined(__APPLE__)
    return PLATFORM_MACOS;
#elif defined(_WIN32)
    return PLATFORM_WINDOWS;
#else
    return PLATFORM_UNKNOWN;
#endif
}

const char *get_platform_name(void) {
    switch (get_platform()) {
        case PLATFORM_LINUX: return "Linux";
        case PLATFORM_MACOS: return "macOS";
        case PLATFORM_WINDOWS: return "Windows";
        default: return "Unknown";
    }
}

// Get architecture
arch_t get_arch(void) {
#if defined(__x86_64__) || defined(_M_X64)
    return ARCH_X86_64;
#elif defined(__i386__) || defined(_M_IX86)
    return ARCH_X86;
#elif defined(__aarch64__) || defined(_M_ARM64)
    return ARCH_ARM64;
#elif defined(__arm__) || defined(_M_ARM)
    return ARCH_ARM;
#else
    return ARCH_UNKNOWN;
#endif
}

const char *get_arch_name(void) {
    switch (get_arch()) {
        case ARCH_X86: return "x86";
        case ARCH_X86_64: return "x86_64";
        case ARCH_ARM: return "ARM";
        case ARCH_ARM64: return "ARM64";
        default: return "Unknown";
    }
}
