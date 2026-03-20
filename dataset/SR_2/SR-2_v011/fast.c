float fast_sr2_v011(float *X, float *Y, int n, float alpha) {
    float sumXcb = 0.0;
    float sumX = 0.0;
    float sumYcb = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        sumX += X[i];
        sumYcb += Y[i] * Y[i] * Y[i];
        i++;
    }
    return alpha * sumXcb + alpha * sumX + alpha * sumYcb + (float)n * alpha;
}