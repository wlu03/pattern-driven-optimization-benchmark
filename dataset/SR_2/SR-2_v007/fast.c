float fast_sr2_v007(float *X, float *Y, int n, float alpha) {
    float sumYcb = 0.0;
    float sumYsq = 0.0;
    float sumY = 0.0;
    for (int i = 0; i < n; i++) {
        sumYcb += Y[i] * Y[i] * Y[i];
        sumYsq += Y[i] * Y[i];
        sumY += Y[i];
    }
    return alpha * sumYcb + alpha * sumYsq + (float)n * alpha + (float)n * alpha + alpha * sumY;
}