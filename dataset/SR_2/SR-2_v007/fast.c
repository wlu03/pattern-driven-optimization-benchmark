float fast_sr2_v007(float *X, float *Y, int n, float alpha, float beta, float gamma) {
    float sumXcb = 0.0;
    float sumYsq = 0.0;
    for (int i = 0; i < n; i++) {
        sumXcb += X[i] * X[i] * X[i];
        sumYsq += Y[i] * Y[i];
    }
    return (float)n * beta + gamma * sumXcb + beta * sumXcb + alpha * sumYsq;
}