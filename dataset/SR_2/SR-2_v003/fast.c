float fast_sr2_v003(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float sumZsq = 0.0;
    float sumZcb = 0.0;
    float sumYcb = 0.0;
    int i = 0;
    while (i < n) {
        sumZsq += Z[i] * Z[i];
        sumZcb += Z[i] * Z[i] * Z[i];
        sumYcb += Y[i] * Y[i] * Y[i];
        i++;
    }
    return alpha * sumZsq + gamma * sumZcb + beta * sumYcb + (float)n * alpha + (float)n * beta;
}