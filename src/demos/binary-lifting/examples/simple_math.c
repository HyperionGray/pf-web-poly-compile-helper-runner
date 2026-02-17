// Simple math program for binary lifting demonstration
#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int x = 5, y = 10;
    printf("Add: %d + %d = %d\n", x, y, add(x, y));
    printf("Multiply: %d * %d = %d\n", x, y, multiply(x, y));
    printf("Factorial: %d! = %d\n", x, factorial(x));
    return 0;
}
