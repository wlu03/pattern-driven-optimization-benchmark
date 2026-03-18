#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v006(double *out, double *A, double *B, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = A[i] * B[i];
        double temp2 = temp1 * A[i];
        double result = temp2;
        out[i] = result;
        i++;
    }
}