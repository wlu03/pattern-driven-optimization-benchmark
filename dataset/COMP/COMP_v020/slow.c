#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_comp_v020(double *A, double *B, int rows, int cols, double k) {
    double result = 0;
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (i >= 0 && i < rows && j >= 0 && j < cols) {
                result += k * A[i*cols+j] * A[i*cols+j] + k * B[i*cols+j];
            }
        }
    }
    return result;
}