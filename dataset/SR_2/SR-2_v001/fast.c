float fast_sr2_v001(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float sumZcb = 0.0;
    float sumXcb = 0.0;
    float sumX = 0.0;
    int i = 0;
    while (i < n) {
        sumZcb += Z[i] * Z[i] * Z[i];
        sumXcb += X[i] * X[i] * X[i];
        sumX += X[i];
        i++;
    }
    return beta * sumZcb + alpha * sumXcb + beta * sumX + beta * sumX;
}