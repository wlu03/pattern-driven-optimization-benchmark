#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_comp_v007(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0, sumY = 0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * alpha * beta;
}