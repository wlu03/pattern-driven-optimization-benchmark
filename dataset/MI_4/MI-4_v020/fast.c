#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_mi4_v020(double *out, double *A, double *B, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            out[i * cols + j] = A[i * cols + j] + B[i * cols + j];
        }
    }
}