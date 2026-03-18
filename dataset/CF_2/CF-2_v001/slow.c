#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v001(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i * cols + j >= 0 && i >= 0 && i < rows);
}
void slow_cf2_v001(float *matrix, int rows, int cols, float *col_sums) {
    for (int j = 0; j < cols; j++) {
        col_sums[j] = 0;
        for (int i = 0; i < rows; i++) {
            if (cf2_check_v001(i, j, rows, cols)) {
                col_sums[j] += matrix[i * cols + j];
            }
        }
    }
}