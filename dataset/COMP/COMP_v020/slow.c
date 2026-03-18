#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_comp_v020(float *mat, int rows, int cols, int mode) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            if (mode == 1) mat[i * cols + j] *= (float)2.0;
            else if (mode == 2) mat[i * cols + j] += (float)1.0;
            else mat[i * cols + j] -= (float)0.5;
        }
    }
}