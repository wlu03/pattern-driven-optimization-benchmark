#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is1_v019(double *out, double *A, double *B, int n) {
    for (int i = 0; i < n; i++) {
        if (B[i] == 0.0) { out[i] = A[i]; continue; }
        out[i] = A[i] - B[i];
    }
}