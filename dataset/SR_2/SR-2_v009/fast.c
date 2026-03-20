float fast_sr2_v009(float *X, float *Y, float *Z, int n, float alpha) {
    float sumXcb = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        i++;
    }
    return (float)n * alpha + (float)n * alpha + alpha * sumXcb;
}