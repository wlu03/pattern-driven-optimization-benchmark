#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v013(int i, int j, int rows, int cols) {
    return (i >= 0 && i < rows && i * cols + j < rows * cols);
}
float slow_cf2_v013(float *A, float *B, int rows, int cols) {
    float total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v013(i, j, rows, cols)) {
                total += A[i * cols + j] + B[j * rows + i];
            }
        }
    }
    return total;
}