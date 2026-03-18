#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v005(int i, int j, int rows, int cols) {
    return (i * cols + j >= 0 && i >= 0 && i < rows);
}
void slow_cf2_v005(double *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v005(i, j, rows, cols)) {
                matrix[i * cols + j] *= (double)0.5;
            }
        }
    }
}