#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int cf2_check_v006(int i, int j, int rows, int cols);
void slow_cf2_v006(float *matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v006(i, j, rows, cols)) {
                matrix[i * cols + j] *= (float)3.14;
            }
        }
    }
}