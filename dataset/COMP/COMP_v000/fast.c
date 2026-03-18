#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int fast_comp_v000(int *X, int *Y, int n, int alpha, int beta) {
    int sumXsq = 0, sumY = 0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (int)n * alpha * beta;
}