#include <math.h>
/* sin*exp penalty — inner loop blocks compiler from hoisting as loop-invariant */
static float penalty(float a, float b) {
    float r = 0.0;
    for (int k = 1; k <= 20; k++) r += (float)sin(a * k) * (float)exp(-b * k * 0.05);
    return r;
}
__attribute__((noinline))
float slow_sr2_v026(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] + beta * Y[i] + penalty(alpha, beta);
        i++;
    }
    return result;
}