#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_comp_v016(float *mat, float *col_avgs, int rows, int cols) {
    for (int j = 0; j < cols; j++) col_avgs[j] = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            col_avgs[j] += mat[i * cols + j];
        }
    }
    for (int j = 0; j < cols; j++) col_avgs[j] /= (float)rows;
}