#include <math.h>
/* sin*exp penalty — inner loop blocks compiler from hoisting as loop-invariant */
static float penalty(float a, float b) {
    float r = 0.0;
    for (int k = 1; k <= 23; k++) r += (float)sin(a * k) * (float)exp(-b * k * 0.02);
    return r;
}
__attribute__((noinline))
float slow_sr2_v007(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] * X[i] + beta * Y[i] + penalty(alpha, beta);
    }
    return result;
}