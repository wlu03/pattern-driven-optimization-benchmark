float fast_sr2_v014(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta, float gamma) {
    float sumZ = 0.0;
    float sumW = 0.0;
    float sumZsq = 0.0;
    for (int i = 0; i < n; i++) {
        sumZ += Z[i];
        sumW += W[i];
        sumZsq += Z[i] * Z[i];
    }
    return beta * sumZ + (float)n * alpha + (float)n * beta + alpha * sumW + alpha * sumZsq;
}