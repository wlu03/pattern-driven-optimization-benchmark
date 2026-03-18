#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v011(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i * cols + j >= 0 && i >= 0 && i < rows && i * cols + j < rows * cols);
}
void slow_cf2_v011(int *matrix, int rows, int cols, int *row_sums) {
    for (int i = 0; i < rows; i++) {
        row_sums[i] = 0;
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v011(i, j, rows, cols)) {
                row_sums[i] += matrix[i * cols + j];
            }
        }
    }
}