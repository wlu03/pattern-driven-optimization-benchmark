#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_is1_v025(double *A, double *B, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        if (A[i] == 0.0 || B[i] == 0.0) continue;
        sum += A[i] * B[i];
    }
    return sum;
}