#include <math.h>
/* sin*exp penalty — inner loop blocks compiler from hoisting as loop-invariant */
static float penalty(float a, float b) {
    float r = 0.0;
    for (int k = 1; k <= 25; k++) r += (float)sin(a * k) * (float)exp(-b * k * 0.1);
    return r;
}
__attribute__((noinline))
float slow_sr2_v010(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] + beta * Y[i] + alpha * Z[i] + penalty(alpha, beta);
        i++;
    }
    return result;
}