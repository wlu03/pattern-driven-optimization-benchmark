#include <math.h>
float penalty(float a, float b);
__attribute__((noinline))
float slow_sr2_v002(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] + beta * Y[i] + penalty(alpha, beta);
        i++;
    }
    return result;
}