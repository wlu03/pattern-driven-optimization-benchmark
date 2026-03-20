float fast_sr2_v009(float *X, float *Y, float *Z, float *W, int n, float alpha) {
    float sumZcb = 0.0;
    float sumWcb = 0.0;
    float sumZ = 0.0;
    int i = 0;
    while (i < n) {
        sumZcb += Z[i] * Z[i] * Z[i];
        sumWcb += W[i] * W[i] * W[i];
        sumZ += Z[i];
        i++;
    }
    return (float)n * alpha + alpha * sumZcb + alpha * sumWcb + alpha * sumZ + (float)n * alpha;
}