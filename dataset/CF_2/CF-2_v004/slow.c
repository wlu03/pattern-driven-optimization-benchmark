#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v004(int i, int j, int rows, int cols) {
    return (i * cols + j < rows * cols && j >= 0 && j < cols && i * cols + j >= 0 && i >= 0 && i < rows);
}
float slow_cf2_v004(float *A, float *B, int rows, int cols) {
    float total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v004(i, j, rows, cols)) {
                total += A[i * cols + j] + B[j * rows + i];
            }
        }
    }
    return total;
}