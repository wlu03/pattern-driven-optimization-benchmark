#include <math.h>
double penalty(double a, double b);
__attribute__((noinline))
double fast_sr2_v025(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0;
    double sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
        i++;
    }
    return alpha * sumXsq + beta * sumY + (double)n * penalty(alpha, beta);
}