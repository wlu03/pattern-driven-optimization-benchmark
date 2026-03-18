#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v028(int i, int j, int rows, int cols) {
    return (i * cols + j < rows * cols && i >= 0 && i < rows);
}
void slow_cf2_v028(float *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v028(i, j, rows, cols)) {
                matrix[i * cols + j] *= (float)3.14;
            }
        }
    }
}