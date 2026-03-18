#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int fast_comp_v025(int *A, int *B, int n, int k, int mode) {
    int sumA = 0, sumB = 0;
    if (mode == 1) {
        for (int i = 0; i < n; i++) { sumA += A[i]; sumB += B[i]; }
        return sumA + sumB * k;
    } else if (mode == 2) {
        for (int i = 0; i < n; i++) { sumA += A[i]; sumB += B[i]; }
        return sumA - sumB * k;
    } else {
        int sumAB = 0;
        for (int i = 0; i < n; i++) sumAB += A[i] * B[i];
        return sumAB * k;
    }
}