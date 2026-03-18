#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_ds3_v005(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        double t = A[i] + B[i];
        out[i] = (t * 3.0 - B[i]) * A[i];
    }
}