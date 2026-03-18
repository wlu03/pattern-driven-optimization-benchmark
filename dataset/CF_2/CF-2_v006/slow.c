#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v006(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i * cols + j >= 0 && i * cols + j < rows * cols);
}
void slow_cf2_v006(int *matrix, int rows, int cols, int *col_sums) {
    for (int j = 0; j < cols; j++) {
        col_sums[j] = 0;
        for (int i = 0; i < rows; i++) {
            if (cf2_check_v006(i, j, rows, cols)) {
                col_sums[j] += matrix[i * cols + j];
            }
        }
    }
}