#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_hr1_v017(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        double t = A[i] - B[i];
        double u = t - A[i];
        out[i] = u * u - B[i];
    }
}