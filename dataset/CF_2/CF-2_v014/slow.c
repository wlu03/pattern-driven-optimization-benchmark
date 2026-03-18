#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int cf2_check_v014(int i, int j, int rows, int cols);
void slow_cf2_v014(double *matrix, int rows, int cols, double *row_sums) {
    for (int i = 0; i < rows; i++) {
        row_sums[i] = 0;
        for (int j = 0; j < cols; j++) {
            if (cf2_check_v014(i, j, rows, cols)) {
                row_sums[i] += matrix[i * cols + j];
            }
        }
    }
}