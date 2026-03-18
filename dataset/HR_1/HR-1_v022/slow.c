#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v022(double *out, double *A, double *B, double *C, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = A[i] - B[i];
        double temp2 = temp1 * C[i];
        double temp3 = temp2 - A[i];
        double temp4 = temp3 - B[i];
        double temp5 = temp4 + C[i];
        double temp6 = temp5 + A[i];
        double result = temp6;
        out[i] = result;
        i++;
    }
}