#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v011(double *out, double *A, double *B, double *C, int n) {
    for (int i = 0; i < n; i++) {
        double temp1 = A[i] + B[i];
        double temp2 = temp1 + C[i];
        double temp3 = temp2 - A[i];
        double temp4 = temp3 - A[i];
        double result = temp4;
        out[i] = result;
    }
}