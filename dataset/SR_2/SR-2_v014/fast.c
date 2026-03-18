#include <math.h>
static double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 12; k++) r += (double)sin(a * k) * (double)exp(-b * k * 0.02);
    return r;
}
__attribute__((noinline))
double fast_sr2_v014(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0;
    double sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * penalty(alpha, beta);
}