#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_comp_v020(double *A, double *B, int rows, int cols, double k) {
    double sumAsq = 0, sumB = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int idx = i*cols+j;
            sumAsq += A[idx] * A[idx];
            sumB += B[idx];
        }
    }
    return k * sumAsq + k * sumB;
}