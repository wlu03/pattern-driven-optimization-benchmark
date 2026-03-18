#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_mi2_v023(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        double t = A[i] * A[i] + B[i];
        out[i] = t * t + B[i];
    }
}