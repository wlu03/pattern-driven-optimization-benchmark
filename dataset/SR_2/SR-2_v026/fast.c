#include <math.h>
static float penalty(float a, float b) {
    float r = 0.0;
    for (int k = 1; k <= 20; k++) r += (float)sin(a * k) * (float)exp(-b * k * 0.05);
    return r;
}
__attribute__((noinline))
float fast_sr2_v026(float *X, float *Y, int n, float alpha, float beta) {
    float sumXsq = 0.0;
    float sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
        i++;
    }
    return alpha * sumXsq + beta * sumY + (double)n * penalty(alpha, beta);
}