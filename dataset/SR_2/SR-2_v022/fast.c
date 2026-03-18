#include <math.h>
double penalty(double a, double b);
__attribute__((noinline))
double fast_sr2_v022(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double sumXsq = 0.0;
    double sumY = 0.0;
    double sumZ = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
        sumZ += Z[i];
    }
    return alpha * sumXsq + beta * sumY + alpha * sumZ + (double)n * penalty(alpha, beta);
}