#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_comp_v020(float *mat, int rows, int cols, int mode) {
    if (mode == 1) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] *= (float)2.0;
    } else if (mode == 2) {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] += (float)1.0;
    } else {
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++) mat[i * cols + j] -= (float)0.5;
    }
}