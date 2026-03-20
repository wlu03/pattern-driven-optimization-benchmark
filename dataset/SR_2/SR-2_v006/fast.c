float fast_sr2_v006(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta) {
    float sumYcb = 0.0;
    float sumXcb = 0.0;
    int i = 0;
    while (i < n) {
        sumYcb += Y[i] * Y[i] * Y[i];
        sumXcb += X[i] * X[i] * X[i];
        i++;
    }
    return beta * sumYcb + beta * sumXcb;
}