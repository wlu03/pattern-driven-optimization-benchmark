#include <math.h>
float penalty(float a, float b);
__attribute__((noinline))
float fast_sr2_v019(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float sumXsq = 0.0;
    float sumY = 0.0;
    float sumZ = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
        sumZ += Z[i];
    }
    return alpha * sumXsq + beta * sumY + alpha * sumZ + (double)n * penalty(alpha, beta);
}