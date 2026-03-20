float fast_sr2_v000(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float sumY = 0.0;
    float sumYcb = 0.0;
    float sumX = 0.0;
    for (int i = 0; i < n; i++) {
        sumY += Y[i];
        sumYcb += Y[i] * Y[i] * Y[i];
        sumX += X[i];
    }
    return gamma * sumY + beta * sumYcb + beta * sumX + alpha * sumYcb + (float)n * gamma;
}