float fast_sr2_v008(float *X, float *Y, int n, float alpha, float beta, float gamma) {
    float sumX = 0.0;
    float sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumX += X[i];
        sumY += Y[i];
    }
    return alpha * sumX + (float)n * beta + beta * sumY + alpha * sumY + (float)n * alpha;
}