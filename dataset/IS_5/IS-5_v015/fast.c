#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is5_v015(float *out, float *A, float *B, float *C, int n) {
    int no_alias = (out + n <= A || A + n <= out) && (out + n <= B || B + n <= out) && (out + n <= C || C + n <= out);
    if (no_alias) {
        // Non-aliasing: cast to restrict-qualified locals
        // so the compiler can emit unguarded SIMD
        float * __restrict__ ro = out;
        const float * __restrict__ rA = (const float * __restrict__)A;
        const float * __restrict__ rB = (const float * __restrict__)B;
        const float * __restrict__ rC = (const float * __restrict__)C;
        for (int i = 0; i < n; i++) {
            ro[i] = rA[i] * rA[i] + rB[i] * rB[i] - rC[i] * 0.5f;
        }
    } else {
        // Aliasing fallback (rare)
    for (int i = 0; i < n; i++) {
        out[i] = A[i] * A[i] + B[i] * B[i] - C[i] * 0.5f;
    }
    }
}