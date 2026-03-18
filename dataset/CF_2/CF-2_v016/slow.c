#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v016(int i, int j, int rows, int cols) {
    return (i >= 0 && i < rows && i * cols + j >= 0 && i * cols + j < rows * cols && j >= 0 && j < cols);
}
void slow_cf2_v016(float *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v016(i, j, rows, cols)) {
                matrix[i * cols + j] *= (float)0.5;
            }
        }
    }
}