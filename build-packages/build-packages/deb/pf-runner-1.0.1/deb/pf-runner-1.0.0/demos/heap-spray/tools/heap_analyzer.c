/**
 * Heap Analysis Tool
 * 
 * This tool provides utilities for analyzing heap state and
 * detecting potential heap spray patterns in memory.
 * 
 * FOR EDUCATIONAL AND DEFENSIVE PURPOSES
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include "../src/heap_spray.h"

#ifdef __linux__
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#endif

// Detection thresholds
#define REPETITION_THRESHOLD 0.8  // 80% repetition indicates possible spray
#define MIN_ALLOCATIONS 10        // Minimum allocations to consider spray
#define PATTERN_SIZE 16           // Size of pattern to check

typedef struct {
    size_t num_allocations;
    size_t total_size;
    double repetition_score;
    bool likely_spray;
    uint8_t common_byte;
    size_t pattern_length;
} spray_detection_result_t;

/**
 * Calculate entropy of a memory region
 * Low entropy suggests repetitive patterns (potential spray)
 */
double calculate_entropy(const uint8_t *data, size_t size) {
    if (!data || size == 0) return 0.0;
    
    // Count byte frequencies
    size_t freq[256] = {0};
    for (size_t i = 0; i < size; i++) {
        freq[data[i]]++;
    }
    
    // Calculate Shannon entropy
    double entropy = 0.0;
    for (int i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            double p = (double)freq[i] / size;
            entropy -= p * (log(p) / log(2.0));
        }
    }
    
    return entropy;
}

/**
 * Detect repetitive patterns in memory
 */
double detect_pattern_repetition(const uint8_t *data, size_t size) {
    if (!data || size < PATTERN_SIZE * 2) return 0.0;
    
    // Take first PATTERN_SIZE bytes as reference pattern
    uint8_t pattern[PATTERN_SIZE];
    memcpy(pattern, data, PATTERN_SIZE);
    
    // Count how many times pattern repeats
    size_t matches = 0;
    size_t total_checks = (size - PATTERN_SIZE) / PATTERN_SIZE;
    
    for (size_t i = 0; i < total_checks; i++) {
        if (memcmp(data + (i * PATTERN_SIZE), pattern, PATTERN_SIZE) == 0) {
            matches++;
        }
    }
    
    return (double)matches / total_checks;
}

/**
 * Find most common byte in data
 */
uint8_t find_common_byte(const uint8_t *data, size_t size) {
    if (!data || size == 0) return 0;
    
    size_t freq[256] = {0};
    for (size_t i = 0; i < size; i++) {
        freq[data[i]]++;
    }
    
    uint8_t common = 0;
    size_t max_freq = 0;
    for (int i = 0; i < 256; i++) {
        if (freq[i] > max_freq) {
            max_freq = freq[i];
            common = i;
        }
    }
    
    return common;
}

/**
 * Analyze heap spray result for patterns
 */
spray_detection_result_t analyze_spray_pattern(const heap_spray_result_t *spray) {
    spray_detection_result_t result = {0};
    
    if (!spray || !spray->allocations || spray->num_allocations == 0) {
        return result;
    }
    
    result.num_allocations = spray->num_allocations;
    result.total_size = spray->total_bytes;
    
    // Analyze first allocation for patterns
    if (spray->allocations[0]) {
        double entropy = calculate_entropy(spray->allocations[0], 256);
        double repetition = detect_pattern_repetition(spray->allocations[0], 256);
        result.common_byte = find_common_byte(spray->allocations[0], 256);
        
        result.repetition_score = repetition;
        
        // Determine if likely spray
        result.likely_spray = (result.num_allocations >= MIN_ALLOCATIONS) &&
                             (repetition >= REPETITION_THRESHOLD || entropy < 2.0);
    }
    
    return result;
}

/**
 * Print analysis report
 */
void print_analysis_report(const spray_detection_result_t *result) {
    if (!result) return;
    
    printf("\n╔═══════════════════════════════════════════════════════╗\n");
    printf("║           HEAP SPRAY DETECTION ANALYSIS              ║\n");
    printf("╚═══════════════════════════════════════════════════════╝\n\n");
    
    printf("Number of allocations: %zu\n", result->num_allocations);
    printf("Total size: %zu bytes (%.2f MB)\n", 
           result->total_size, result->total_size / (1024.0 * 1024.0));
    printf("Pattern repetition score: %.2f%%\n", result->repetition_score * 100);
    printf("Most common byte: 0x%02X ('%c')\n", 
           result->common_byte,
           (result->common_byte >= 32 && result->common_byte < 127) ? 
           result->common_byte : '.');
    
    printf("\n");
    if (result->likely_spray) {
        printf("⚠️  HIGH CONFIDENCE: Heap spray pattern detected!\n\n");
        printf("Indicators:\n");
        if (result->num_allocations >= MIN_ALLOCATIONS) {
            printf("  ✓ Many similar allocations (%zu)\n", result->num_allocations);
        }
        if (result->repetition_score >= REPETITION_THRESHOLD) {
            printf("  ✓ High pattern repetition (%.0f%%)\n", 
                   result->repetition_score * 100);
        }
    } else {
        printf("✓ No obvious heap spray pattern detected\n");
    }
    
    printf("\n");
}

/**
 * Compare two spray patterns
 */
void compare_spray_patterns(const heap_spray_result_t *spray1,
                           const heap_spray_result_t *spray2) {
    printf("\n╔═══════════════════════════════════════════════════════╗\n");
    printf("║           SPRAY PATTERN COMPARISON                   ║\n");
    printf("╚═══════════════════════════════════════════════════════╝\n\n");
    
    printf("                        Spray #1      Spray #2\n");
    printf("Allocations:            %-12zu %-12zu\n", 
           spray1->num_allocations, spray2->num_allocations);
    printf("Total size (MB):        %-12.2f %-12.2f\n",
           spray1->total_bytes / (1024.0 * 1024.0),
           spray2->total_bytes / (1024.0 * 1024.0));
    printf("Address range (MB):     %-12.2f %-12.2f\n",
           (spray1->max_addr - spray1->min_addr) / (1024.0 * 1024.0),
           (spray2->max_addr - spray2->min_addr) / (1024.0 * 1024.0));
    
    printf("\n");
}

/**
 * Demonstrate spray detection
 */
void demonstrate_detection(void) {
    printf("\n===== HEAP SPRAY DETECTION DEMONSTRATION =====\n\n");
    
    // Create a spray with obvious pattern
    printf("[*] Creating heap spray with repetitive pattern...\n");
    uint8_t pattern[] = {0x41, 0x41, 0x41, 0x41}; // 'AAAA'
    heap_spray_result_t *spray1 = heap_spray_basic(4096, 30, pattern, sizeof(pattern));
    
    if (spray1) {
        spray_detection_result_t detection = analyze_spray_pattern(spray1);
        print_analysis_report(&detection);
        heap_spray_cleanup(spray1);
    }
    
    // Create a spray with random data (less obvious)
    printf("\n[*] Creating heap spray with pseudo-random data...\n");
    uint8_t random_pattern[16];
    for (int i = 0; i < 16; i++) {
        random_pattern[i] = rand() % 256;
    }
    heap_spray_result_t *spray2 = heap_spray_basic(4096, 30, 
                                                    random_pattern, sizeof(random_pattern));
    
    if (spray2) {
        spray_detection_result_t detection = analyze_spray_pattern(spray2);
        print_analysis_report(&detection);
        heap_spray_cleanup(spray2);
    }
}

/**
 * Demonstrate defensive monitoring
 */
void demonstrate_monitoring(void) {
    printf("\n===== DEFENSIVE HEAP MONITORING =====\n\n");
    
    printf("In a production system, you would monitor for:\n");
    printf("1. Rapid allocation of many similar-sized chunks\n");
    printf("2. Low entropy in allocated memory\n");
    printf("3. Repetitive patterns across allocations\n");
    printf("4. Unusual heap growth patterns\n\n");
    
    printf("Simulating normal allocations...\n");
    void *normal_allocs[5];
    for (int i = 0; i < 5; i++) {
        normal_allocs[i] = malloc(100 + (i * 50));
    }
    
    heap_stats_t stats1;
    if (heap_get_stats(&stats1)) {
        printf("Heap state after normal allocations:\n");
        heap_print_stats(&stats1);
    }
    
    printf("\nSimulating suspicious spray pattern...\n");
    void *spray_allocs[50];
    for (int i = 0; i < 50; i++) {
        spray_allocs[i] = malloc(4096);
        if (spray_allocs[i]) {
            memset(spray_allocs[i], 0x90, 4096);
        }
    }
    
    heap_stats_t stats2;
    if (heap_get_stats(&stats2)) {
        printf("Heap state after spray:\n");
        heap_print_stats(&stats2);
        
        size_t growth = stats2.total_allocated_bytes - stats1.total_allocated_bytes;
        printf("\n⚠️  Detected rapid heap growth: %zu bytes (%.2f MB)\n",
               growth, growth / (1024.0 * 1024.0));
        printf("This pattern is consistent with heap spraying!\n");
    }
    
    // Cleanup
    for (int i = 0; i < 5; i++) free(normal_allocs[i]);
    for (int i = 0; i < 50; i++) if (spray_allocs[i]) free(spray_allocs[i]);
}

int main(void) {
    printf("\n");
    printf("╔═══════════════════════════════════════════════════════════╗\n");
    printf("║            HEAP SPRAY ANALYSIS TOOL                      ║\n");
    printf("║                                                           ║\n");
    printf("║  This tool demonstrates techniques for detecting and     ║\n");
    printf("║  analyzing heap spray patterns. Useful for:              ║\n");
    printf("║  - Security researchers                                  ║\n");
    printf("║  - Defenders implementing monitoring                     ║\n");
    printf("║  - Understanding exploitation techniques                 ║\n");
    printf("║                                                           ║\n");
    printf("║  FOR EDUCATIONAL PURPOSES ONLY                           ║\n");
    printf("╚═══════════════════════════════════════════════════════════╝\n");
    
    srand(time(NULL));
    
    // Run demonstrations
    demonstrate_detection();
    demonstrate_monitoring();
    
    printf("\n");
    printf("══════════════════════════════════════════════════════════\n");
    printf("Detection Techniques Summary:\n\n");
    printf("Static Analysis:\n");
    printf("  ✓ Pattern repetition detection\n");
    printf("  ✓ Entropy calculation\n");
    printf("  ✓ Common byte analysis\n\n");
    printf("Dynamic Monitoring:\n");
    printf("  ✓ Allocation rate monitoring\n");
    printf("  ✓ Heap growth tracking\n");
    printf("  ✓ Size distribution analysis\n\n");
    printf("Mitigation Strategies:\n");
    printf("  • Implement allocation rate limits\n");
    printf("  • Monitor for unusual patterns\n");
    printf("  • Use hardened allocators\n");
    printf("  • Enable ASLR and memory tagging\n");
    printf("══════════════════════════════════════════════════════════\n\n");
    
    return 0;
}
