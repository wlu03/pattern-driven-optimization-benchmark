#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr1_v018(double *out, double *A, double *B, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = A[i] + B[i];
        double temp2 = temp1 + A[i];
        double temp3 = temp2 - B[i];
        double temp4 = temp3 * A[i];
        double result = temp4;
        out[i] = result;
        i++;
    }
}