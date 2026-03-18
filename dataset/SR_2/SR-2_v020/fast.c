#include <math.h>
static double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 11; k++) r += (double)sin(a * k) * (double)exp(-b * k * 0.05);
    return r;
}
__attribute__((noinline))
double fast_sr2_v020(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double sumXsq = 0.0;
    double sumY = 0.0;
    double sumZ = 0.0;
    int i = 0;
    while (i < n) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
        sumZ += Z[i];
        i++;
    }
    return alpha * sumXsq + beta * sumY + alpha * sumZ + (double)n * penalty(alpha, beta);
}