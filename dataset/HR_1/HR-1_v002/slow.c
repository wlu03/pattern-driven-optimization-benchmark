#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v002(double *out, double *A, double *B, double *C, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = A[i] - B[i];
        double temp2 = temp1 - C[i];
        double temp3 = temp2 + A[i];
        double result = temp3;
        out[i] = result;
        i++;
    }
}