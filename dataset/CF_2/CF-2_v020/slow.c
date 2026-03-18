#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v020(int i, int j, int rows, int cols) {
    return (i * cols + j >= 0 && i * cols + j < rows * cols && i >= 0 && i < rows);
}
double slow_cf2_v020(double *A, double *B, int rows, int cols) {
    double total = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v020(i, j, rows, cols)) {
                total += A[i * cols + j] + B[j * rows + i];
            }
        }
    }
    return total;
}