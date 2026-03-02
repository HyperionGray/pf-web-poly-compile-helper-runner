#include <stdio.h>
#include <unistd.h>

int main() {
    printf("Target application starting...\n");
    printf("PID: %d\n", getpid());
    
    for (int i = 0; i < 5; i++) {
        printf("Target app iteration %d\n", i + 1);
        sleep(1);
    }
    
    printf("Target application finished.\n");
    return 0;
}