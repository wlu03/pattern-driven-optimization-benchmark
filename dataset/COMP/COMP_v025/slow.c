#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_comp_v025(double *A, double *B, int n, double k, int mode) {
    double total = 0;
    for (int i = 0; i < n; i++) {
        double val;
        if (mode == 1) val = A[i] + B[i] * k;
        else if (mode == 2) val = A[i] - B[i] * k;
        else val = A[i] * B[i] * k;
        total += val;
    }
    return total;
}