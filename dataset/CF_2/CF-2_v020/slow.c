#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v020(int i, int j, int rows, int cols) {
    return (i >= 0 && i < rows && j >= 0 && j < cols && i * cols + j < rows * cols && i * cols + j >= 0);
}
int slow_cf2_v020(int *A, int *B, int rows, int cols) {
    int total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v020(i, j, rows, cols)) {
                total += A[i * cols + j] + B[j * rows + i];
            }
        }
    }
    return total;
}