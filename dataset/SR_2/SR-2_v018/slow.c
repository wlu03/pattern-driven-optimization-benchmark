#include <math.h>
/* sin*exp penalty — inner loop blocks compiler from hoisting as loop-invariant */
static double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 29; k++) r += (double)sin(a * k) * (double)exp(-b * k * 0.05);
    return r;
}
__attribute__((noinline))
double slow_sr2_v018(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] + beta * Y[i] + alpha * Z[i] + penalty(alpha, beta);
        i++;
    }
    return result;
}