#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fast_cf2_v004(float *A, float *B, int rows, int cols) {
    float total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            total += A[i * cols + j] + B[j * rows + i];
        }
    }
    return total;
}