float fast_sr2_v003(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float sumXcb = 0.0;
    float sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        sumY += Y[i];
        i++;
    }
    return alpha * sumXcb + alpha * sumY + (float)n * beta;
}