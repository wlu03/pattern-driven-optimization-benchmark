#include <math.h>
static float penalty(float a, float b) {
    float r = 0.0;
    for (int k = 1; k <= 27; k++) r += (float)sin(a * k) * (float)exp(-b * k * 0.1);
    return r;
}
__attribute__((noinline))
float fast_sr2_v006(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float sumXsq = 0.0;
    float sumY = 0.0;
    float sumZ = 0.0;
    int i = 0;
    while (i < n) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
        sumZ += Z[i];
        i++;
    }
    return alpha * sumXsq + beta * sumY + alpha * sumZ + (double)n * penalty(alpha, beta);
}