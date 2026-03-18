#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is1_v013(float *y, float *A, float *x, int m, int n) {
    for (int i = 0; i < m; i++) {
        y[i] = 0.0f;
        for (int j = 0; j < n; j++) {
            if (A[i * n + j] == 0.0f) continue;
            y[i] += A[i * n + j] * x[j];
        }
    }
}