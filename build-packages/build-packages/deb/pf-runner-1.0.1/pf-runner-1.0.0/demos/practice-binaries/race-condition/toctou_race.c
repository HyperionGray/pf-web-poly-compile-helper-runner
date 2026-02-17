// Race condition vulnerability practice binary
// Purpose: Learn TOCTOU (Time-of-Check-Time-of-Use) exploitation
// Vulnerability: Race condition in file access check

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <pthread.h>

#define SLEEP_TIME 100000  // 100ms to make race window obvious

char *target_file = "/tmp/race_target";
int access_granted = 0;

void secret_data() {
    printf("\n🔐 SECRET DATA ACCESSED! 🔐\n");
    printf("Race condition exploitation successful!\n");
    printf("You bypassed the access control check!\n");
}

void *file_swapper(void *arg) {
    char *swap_file = (char*)arg;
    
    // Continuously swap the symlink during the race window
    for (int i = 0; i < 100; i++) {
        unlink(target_file);
        symlink(swap_file, target_file);
        usleep(10000);  // 10ms
    }
    
    return NULL;
}

void vulnerable_file_access(char *filename) {
    printf("\n=== Checking file access ===\n");
    
    // STEP 1: Check if file is safe to read (Time-of-Check)
    struct stat st;
    if (stat(target_file, &st) != 0) {
        printf("❌ File doesn't exist: %s\n", target_file);
        return;
    }
    
    printf("✓ File exists, checking permissions...\n");
    
    // Check if we own the file
    if (st.st_uid != getuid()) {
        printf("❌ You don't own this file!\n");
        return;
    }
    
    printf("✓ Permission check passed!\n");
    printf("⏰ Sleeping to simulate processing... (RACE WINDOW)\n");
    
    // VULNERABILITY: Delay between check and use (TOCTOU)
    usleep(SLEEP_TIME);
    
    // STEP 2: Open and read the file (Time-of-Use)
    printf("Opening file: %s\n", target_file);
    FILE *fp = fopen(target_file, "r");
    if (!fp) {
        printf("❌ Failed to open file!\n");
        return;
    }
    
    printf("✓ File opened, reading contents...\n");
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), fp)) {
        printf("  %s", buffer);
    }
    
    fclose(fp);
    access_granted = 1;
    
    if (access_granted) {
        secret_data();
    }
}

void setup_race() {
    // Create a safe file owned by us
    FILE *safe = fopen("/tmp/safe_file", "w");
    if (safe) {
        fprintf(safe, "This is a safe file you own.\n");
        fclose(safe);
    }
    
    // Create a secret file with restricted permissions
    FILE *secret = fopen("/tmp/secret_file", "w");
    if (secret) {
        fprintf(secret, "🔒 THIS IS SECRET DATA 🔒\n");
        fprintf(secret, "You shouldn't be able to read this!\n");
        fclose(secret);
    }
    
    // Initially point to safe file
    unlink(target_file);
    symlink("/tmp/safe_file", target_file);
    
    printf("Setup complete:\n");
    printf("  Safe file: /tmp/safe_file (owned by you)\n");
    printf("  Secret file: /tmp/secret_file (protected)\n");
    printf("  Target symlink: %s -> /tmp/safe_file\n", target_file);
}

int main(int argc, char *argv[]) {
    printf("=== Race Condition (TOCTOU) Practice ===\n");
    
    if (argc < 2) {
        printf("\nUsage: %s <command>\n", argv[0]);
        printf("Commands:\n");
        printf("  setup          - Create test files\n");
        printf("  access         - Access file with race window\n");
        printf("  exploit        - Run exploit with file swapping\n");
        printf("\nPractice objectives:\n");
        printf("1. Understand Time-of-Check-Time-of-Use (TOCTOU)\n");
        printf("2. Identify race window between check and use\n");
        printf("3. Exploit by swapping symlink during race window\n");
        printf("4. Bypass access control to read secret file\n");
        printf("\nExploit steps:\n");
        printf("  Terminal 1: %s setup\n", argv[0]);
        printf("  Terminal 2: %s access\n", argv[0]);
        printf("  Terminal 1 (during sleep): ln -sf /tmp/secret_file %s\n", target_file);
        return 1;
    }
    
    if (strcmp(argv[1], "setup") == 0) {
        setup_race();
    } else if (strcmp(argv[1], "access") == 0) {
        vulnerable_file_access(target_file);
    } else if (strcmp(argv[1], "exploit") == 0) {
        setup_race();
        
        // Start thread to swap symlink
        pthread_t thread;
        pthread_create(&thread, NULL, file_swapper, "/tmp/secret_file");
        
        // Try to access with race condition
        usleep(50000);  // Let swapper start
        vulnerable_file_access(target_file);
        
        pthread_join(thread, NULL);
    } else {
        printf("Invalid command!\n");
    }
    
    return 0;
}
