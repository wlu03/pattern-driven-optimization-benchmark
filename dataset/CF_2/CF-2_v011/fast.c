#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_cf2_v011(double *matrix, int rows, int cols, double *row_sums) {
    for (int i = 0; i < rows; i++) {
        row_sums[i] = 0;
        for (int j = 0; j < cols; j++) {
            row_sums[i] += matrix[i * cols + j];
        }
    }
}