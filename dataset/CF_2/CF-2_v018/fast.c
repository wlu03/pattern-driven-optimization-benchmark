#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_cf2_v018(float *matrix, int rows, int cols, float *col_sums) {
    for (int j = 0; j < cols; j++) {
        col_sums[j] = 0;
        for (int i = 0; i < rows; i++) {
            col_sums[j] += matrix[i * cols + j];
        }
    }
}