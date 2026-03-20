float fast_sr2_v013(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float sumYsq = 0.0;
    float sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumYsq += Y[i] * Y[i];
        sumY += Y[i];
        i++;
    }
    return beta * sumYsq + alpha * sumY;
}