#include <math.h>
float penalty(float a, float b);
__attribute__((noinline))
float fast_sr2_v013(float *X, float *Y, float *Z, int n, float alpha, float beta) {
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