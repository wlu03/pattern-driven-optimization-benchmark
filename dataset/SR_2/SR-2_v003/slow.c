#include <math.h>
float penalty(float a, float b);
__attribute__((noinline))
float slow_sr2_v003(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] * X[i] + beta * Y[i] + penalty(alpha, beta);
    }
    return result;
}