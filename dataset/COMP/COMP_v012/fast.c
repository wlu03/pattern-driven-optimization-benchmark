#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_comp_v012(double *A, double *B, int n, double k, int mode) {
    double sumA = 0, sumB = 0;
    if (mode == 1) {
        for (int i = 0; i < n; i++) { sumA += A[i]; sumB += B[i]; }
        return sumA + sumB * k;
    } else if (mode == 2) {
        for (int i = 0; i < n; i++) { sumA += A[i]; sumB += B[i]; }
        return sumA - sumB * k;
    } else {
        double sumAB = 0;
        for (int i = 0; i < n; i++) sumAB += A[i] * B[i];
        return sumAB * k;
    }
}