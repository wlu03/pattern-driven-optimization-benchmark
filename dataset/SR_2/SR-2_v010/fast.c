float fast_sr2_v010(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta) {
    float sumXsq = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
    }
    return beta * sumXsq + (float)n * beta;
}