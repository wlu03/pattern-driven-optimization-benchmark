#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is5_v019(double *out, double *A, double *B, double *C, int n) {
    int no_alias = (out + n <= A || A + n <= out) && (out + n <= B || B + n <= out) && (out + n <= C || C + n <= out);
    if (no_alias) {
        // Non-aliasing: cast to restrict-qualified locals
        // so the compiler can emit unguarded SIMD
        double * __restrict__ ro = out;
        const double * __restrict__ rA = (const double * __restrict__)A;
        const double * __restrict__ rB = (const double * __restrict__)B;
        const double * __restrict__ rC = (const double * __restrict__)C;
        for (int i = 0; i < n; i++) {
            ro[i] = rA[i] * rA[i] + rB[i] * rB[i] - rC[i] * 0.5;
        }
    } else {
        // Aliasing fallback (rare)
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * B[i] - C[i] * 0.5;
    }
    }
}