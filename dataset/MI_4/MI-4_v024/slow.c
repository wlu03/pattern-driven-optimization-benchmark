#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float slow_mi4_v024(float *matrix, int rows, int cols) {
    float total = 0;
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            total += matrix[i * cols + j];
        }
    }
    return total;
}