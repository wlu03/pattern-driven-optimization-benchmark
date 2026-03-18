#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v025(int i, int j, int rows, int cols) {
    return (i >= 0 && i < rows && i * cols + j < rows * cols);
}
void slow_cf2_v025(float *matrix, int rows, int cols, float *row_sums) {
    for (int i = 0; i < rows; i++) {
        row_sums[i] = 0;
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v025(i, j, rows, cols)) {
                row_sums[i] += matrix[i * cols + j];
            }
        }
    }
}