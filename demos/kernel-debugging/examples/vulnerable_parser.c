#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Parse function with many if/else statements
int parse_config(const char *input) {
    if (input == NULL) {
        return -1;
    }
    
    if (strcmp(input, "option1") == 0) {
        return 1;
    } else if (strcmp(input, "option2") == 0) {
        return 2;
    } else if (strcmp(input, "option3") == 0) {
        return 3;
    } else if (strcmp(input, "option4") == 0) {
        return 4;
    } else if (strcmp(input, "option5") == 0) {
        return 5;
    } else if (strcmp(input, "option6") == 0) {
        return 6;
    } else if (strcmp(input, "option7") == 0) {
        return 7;
    } else if (strcmp(input, "option8") == 0) {
        return 8;
    } else if (strcmp(input, "option9") == 0) {
        return 9;
    } else if (strcmp(input, "option10") == 0) {
        return 10;
    } else {
        return 0;
    }
}

// A long function that "goes on forever"
void process_data(char *buffer, int size) {
    int i, j, k;
    char temp[1024];
    
    // Many nested loops and operations
    for (i = 0; i < size; i++) {
        for (j = 0; j < 100; j++) {
            for (k = 0; k < 50; k++) {
                temp[k] = buffer[i] ^ j;
            }
        }
        
        if (buffer[i] == 'A') {
            buffer[i] = 'a';
        } else if (buffer[i] == 'B') {
            buffer[i] = 'b';
        } else if (buffer[i] == 'C') {
            buffer[i] = 'c';
        } else if (buffer[i] == 'D') {
            buffer[i] = 'd';
        } else if (buffer[i] == 'E') {
            buffer[i] = 'e';
        }
        
        for (j = 0; j < 10; j++) {
            buffer[i] = (buffer[i] + j) % 256;
        }
    }
    
    // More processing
    for (i = 0; i < size - 1; i++) {
        if (buffer[i] > buffer[i+1]) {
            char tmp = buffer[i];
            buffer[i] = buffer[i+1];
            buffer[i+1] = tmp;
        }
    }
}

// Parse function with user input handling
int parse_user_input(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        return -1;
    }
    
    char buffer[1024];
    while (fgets(buffer, sizeof(buffer), fp)) {
        // Remove newline
        buffer[strcspn(buffer, "\n")] = 0;
        
        // Parse each line
        if (strstr(buffer, "name=") == buffer) {
            printf("Name: %s\n", buffer + 5);
        } else if (strstr(buffer, "value=") == buffer) {
            printf("Value: %s\n", buffer + 6);
        } else if (strstr(buffer, "data=") == buffer) {
            printf("Data: %s\n", buffer + 5);
        }
    }
    
    fclose(fp);
    return 0;
}

// Vulnerable parse function (buffer overflow potential)
void parse_command(char *input) {
    char cmd[128];
    char arg[128];
    
    // Dangerous: no bounds checking
    sscanf(input, "%s %s", cmd, arg);
    
    if (strcmp(cmd, "set") == 0) {
        printf("Setting: %s\n", arg);
    } else if (strcmp(cmd, "get") == 0) {
        printf("Getting: %s\n", arg);
    } else if (strcmp(cmd, "delete") == 0) {
        printf("Deleting: %s\n", arg);
    } else if (strcmp(cmd, "update") == 0) {
        printf("Updating: %s\n", arg);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        return 1;
    }
    
    // Test parse functions
    int result = parse_config("option5");
    printf("Config result: %d\n", result);
    
    // Test long function
    char test_data[256];
    memset(test_data, 'A', sizeof(test_data));
    process_data(test_data, 100);
    
    // Test user input parsing
    parse_user_input(argv[1]);
    
    // Test command parsing
    if (argc > 2) {
        parse_command(argv[2]);
    }
    
    return 0;
}
