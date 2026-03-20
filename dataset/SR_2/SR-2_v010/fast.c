float fast_sr2_v010(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta, float gamma) {
    float sumZsq = 0.0;
    float sumWsq = 0.0;
    float sumXcb = 0.0;
    int i = 0;
    while (i < n) {
        sumZsq += Z[i] * Z[i];
        sumWsq += W[i] * W[i];
        sumXcb += X[i] * X[i] * X[i];
        i++;
    }
    return beta * sumZsq + gamma * sumWsq + beta * sumXcb;
}