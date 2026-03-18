#include <math.h>
double penalty(double a, double b);
__attribute__((noinline))
double slow_sr2_v021(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] + beta * Y[i] + alpha * Z[i] + penalty(alpha, beta);
        i++;
    }
    return result;
}