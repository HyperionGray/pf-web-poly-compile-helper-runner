// String operations for binary lifting demonstration
#include <stdio.h>
#include <string.h>

int string_length(const char* str) {
    int len = 0;
    while (str[len] != '\0') {
        len++;
    }
    return len;
}

void reverse_string(char* str) {
    int len = strlen(str);
    for (int i = 0; i < len / 2; i++) {
        char temp = str[i];
        str[i] = str[len - 1 - i];
        str[len - 1 - i] = temp;
    }
}

int main() {
    char buffer[100] = "Hello World";
    printf("Original: %s\n", buffer);
    printf("Length: %d\n", string_length(buffer));
    reverse_string(buffer);
    printf("Reversed: %s\n", buffer);
    return 0;
}
