float fast_sr2_v014(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta, float gamma) {
    float sumX = 0.0;
    for (int i = 0; i < n; i++) {
        sumX += X[i];
    }
    return alpha * sumX + (float)n * gamma;
}