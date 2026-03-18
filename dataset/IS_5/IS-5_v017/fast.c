#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is5_v017(float *out, float *A, float *B, int n) {
    int no_alias = (out + n <= A || A + n <= out) && (out + n <= B || B + n <= out);
    if (no_alias) {
        // Non-aliasing: cast to restrict-qualified locals
        // so the compiler can emit unguarded SIMD
        float * __restrict__ ro = out;
        const float * __restrict__ rA = (const float * __restrict__)A;
        const float * __restrict__ rB = (const float * __restrict__)B;
        for (int i = 0; i < n; i++) {
            ro[i] += rA[i] * 2.0f + rB[i] * 0.5f;
        }
    } else {
        // Aliasing fallback (rare)
    int i = 0;
    while (i < n) {
        out[i] += A[i] * 2.0f + B[i] * 0.5f;
        i++;
    }
    }
}