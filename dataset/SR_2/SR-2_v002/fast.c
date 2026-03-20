float fast_sr2_v002(float *X, float *Y, int n, float alpha, float beta, float gamma) {
    float sumXcb = 0.0;
    float sumX = 0.0;
    float sumXsq = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        sumX += X[i];
        sumXsq += X[i] * X[i];
        i++;
    }
    return beta * sumXcb + beta * sumX + beta * sumX + gamma * sumXsq;
}