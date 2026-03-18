#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_is1_v010(double *C, double *A, double *B, int m, int k, int n) {
    for (int i = 0; i < m; i++)
        for (int j = 0; j < n; j++) C[i * n + j] = 0.0;
    for (int i = 0; i < m; i++) {
        for (int p = 0; p < k; p++) {
            if (A[i * k + p] == 0.0) continue;
            for (int j = 0; j < n; j++) {
                if (B[p * n + j] == 0.0) continue;
                C[i * n + j] += A[i * k + p] * B[p * n + j];
            }
        }
    }
}