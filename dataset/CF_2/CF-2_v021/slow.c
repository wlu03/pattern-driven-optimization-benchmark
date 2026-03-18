#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v021(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i >= 0 && i < rows && i * cols + j < rows * cols && i * cols + j >= 0);
}
int slow_cf2_v021(int *A, int *B, int rows, int cols) {
    int total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v021(i, j, rows, cols)) {
                total += A[i * cols + j] + B[j * rows + i];
            }
        }
    }
    return total;
}