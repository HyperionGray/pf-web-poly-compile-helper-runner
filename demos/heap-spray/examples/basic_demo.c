/**
 * Basic Heap Spray Demo
 * 
 * This example demonstrates the fundamentals of heap spraying:
 * - Allocating many chunks to fill the heap
 * - Creating predictable memory layouts
 * - Understanding heap address patterns
 * 
 * FOR EDUCATIONAL PURPOSES ONLY
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/heap_spray.h"

void demonstrate_basic_spray(void) {
    printf("\n===== BASIC HEAP SPRAY DEMONSTRATION =====\n\n");
    
    printf("Heap spraying is a technique where an attacker allocates many\n");
    printf("chunks of memory to create a predictable heap layout. This makes\n");
    printf("it easier to exploit memory corruption vulnerabilities.\n\n");
    
    printf("Platform: %s\n", get_platform_name());
    printf("Architecture: %s\n\n", get_arch_name());
    
    // Demonstrate basic spray
    printf("[*] Performing basic heap spray with 50 chunks of 4KB each...\n\n");
    
    heap_spray_result_t *result = heap_spray_basic(4096, 50, NULL, 0);
    
    if (result) {
        heap_spray_print_stats(result);
        heap_visualize_allocations(result);
        
        // Show a few allocation addresses
        printf("Sample allocation addresses:\n");
        for (size_t i = 0; i < 5 && i < result->num_allocations; i++) {
            printf("  Chunk %zu: 0x%lx\n", i, (unsigned long)result->allocations[i]);
        }
        printf("\n");
        
        // Dump first chunk
        printf("Contents of first chunk (first 64 bytes):\n");
        heap_dump_region(result->allocations[0], 64);
        
        heap_spray_cleanup(result);
    }
}

void demonstrate_pattern_spray(void) {
    printf("\n===== PATTERN-BASED HEAP SPRAY =====\n\n");
    
    printf("Attackers often fill sprayed chunks with specific patterns:\n");
    printf("- NOP sleds to increase exploit reliability\n");
    printf("- Shellcode to execute malicious code\n");
    printf("- Return addresses to redirect control flow\n\n");
    
    // Create a NOP sled pattern
    uint8_t pattern[16];
    create_nop_sled(pattern, sizeof(pattern), "x86_64");
    
    printf("[*] Spraying heap with NOP sled pattern...\n\n");
    
    heap_spray_result_t *result = heap_spray_basic(
        8192, 30, pattern, sizeof(pattern));
    
    if (result) {
        heap_spray_print_stats(result);
        
        // Verify pattern
        printf("Verifying pattern in first chunk:\n");
        if (heap_check_pattern(result->allocations[0], pattern, sizeof(pattern))) {
            printf("[+] Pattern correctly placed at 0x%lx\n", 
                   (unsigned long)result->allocations[0]);
        }
        
        heap_dump_region(result->allocations[0], 64);
        
        heap_spray_cleanup(result);
    }
}

void demonstrate_heap_grooming(void) {
    printf("\n===== HEAP GROOMING DEMONSTRATION =====\n\n");
    
    printf("Heap grooming is a technique to create specific memory layouts\n");
    printf("before exploitation. It involves:\n");
    printf("1. Fragmenting the heap with initial allocations\n");
    printf("2. Creating holes of specific sizes\n");
    printf("3. Filling holes with attacker-controlled data\n\n");
    
    heap_groom_config_t groom_config = {
        .initial_allocs = 20,
        .hole_size = 2048,
        .num_holes = 10,
        .target_chunk_size = 2048
    };
    
    printf("[*] Performing heap grooming...\n\n");
    
    heap_spray_result_t *result = heap_groom_prepare(&groom_config);
    
    if (result) {
        heap_spray_print_stats(result);
        
        printf("The heap is now groomed with predictable hole sizes.\n");
        printf("An attacker could place controlled data in these holes.\n\n");
        
        heap_spray_cleanup(result);
    }
}

void demonstrate_heap_stats(void) {
    printf("\n===== HEAP STATISTICS MONITORING =====\n\n");
    
    printf("Understanding heap state is crucial for exploitation:\n");
    printf("- Total allocated memory\n");
    printf("- Heap fragmentation level\n");
    printf("- Available free chunks\n\n");
    
    heap_stats_t stats;
    
    printf("Initial heap state:\n");
    if (heap_get_stats(&stats)) {
        heap_print_stats(&stats);
    } else {
        printf("[!] Heap statistics not available on this platform\n\n");
    }
    
    // Allocate some memory
    printf("[*] Allocating memory...\n");
    void *chunks[10];
    for (int i = 0; i < 10; i++) {
        chunks[i] = malloc(1024 * 100);
    }
    
    printf("\nHeap state after allocations:\n");
    if (heap_get_stats(&stats)) {
        heap_print_stats(&stats);
    }
    
    // Free some memory
    printf("[*] Freeing some memory to create fragmentation...\n");
    for (int i = 0; i < 10; i += 2) {
        free(chunks[i]);
    }
    
    printf("\nHeap state after freeing (fragmented):\n");
    if (heap_get_stats(&stats)) {
        heap_print_stats(&stats);
    }
    
    // Clean up
    for (int i = 1; i < 10; i += 2) {
        free(chunks[i]);
    }
}

int main(void) {
    printf("\n");
    printf("╔════════════════════════════════════════════════════════════╗\n");
    printf("║           HEAP SPRAY EDUCATIONAL DEMONSTRATION            ║\n");
    printf("║                                                            ║\n");
    printf("║  This demo illustrates heap spray techniques used in      ║\n");
    printf("║  memory exploitation. Understanding these techniques      ║\n");
    printf("║  helps both attackers and defenders.                      ║\n");
    printf("║                                                            ║\n");
    printf("║  FOR EDUCATIONAL PURPOSES ONLY                            ║\n");
    printf("╚════════════════════════════════════════════════════════════╝\n");
    
    // Run demonstrations
    demonstrate_basic_spray();
    demonstrate_pattern_spray();
    demonstrate_heap_grooming();
    demonstrate_heap_stats();
    
    printf("\n");
    printf("═══════════════════════════════════════════════════════════\n");
    printf("Demo completed. Key takeaways:\n");
    printf("1. Heap spraying fills memory with attacker-controlled data\n");
    printf("2. Patterns (NOPs, shellcode) increase exploit reliability\n");
    printf("3. Heap grooming creates predictable memory layouts\n");
    printf("4. Monitoring heap state helps understand vulnerability\n");
    printf("═══════════════════════════════════════════════════════════\n\n");
    
    return 0;
}
