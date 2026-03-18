#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int __attribute__((noinline)) cf2_check_v000(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i * cols + j >= 0 && i * cols + j < rows * cols);
}
void slow_cf2_v000(int *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v000(i, j, rows, cols)) {
                matrix[i * cols + j] *= (int)0.5;
            }
        }
    }
}