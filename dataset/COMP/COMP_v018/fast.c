#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_comp_v018(int *out, int *A, int *B, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            out[i*cols+j] = (A[i*cols+j] + B[i*cols+j]) * (int)2.0 + (int)1.0;
        }
    }
}