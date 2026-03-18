#include <math.h>
/* sin*exp penalty — inner loop blocks compiler from hoisting as loop-invariant */
static double penalty(double a, double b) {
    double r = 0.0;
    for (int k = 1; k <= 12; k++) r += (double)sin(a * k) * (double)exp(-b * k * 0.02);
    return r;
}
__attribute__((noinline))
double slow_sr2_v014(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] * X[i] + beta * Y[i] + penalty(alpha, beta);
    }
    return result;
}