float fast_sr2_v008(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float sumYcb = 0.0;
    float sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumYcb += Y[i] * Y[i] * Y[i];
        sumY += Y[i];
        i++;
    }
    return beta * sumYcb + alpha * sumY;
}