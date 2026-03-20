float penalty_sr2_v010(float a, float b);

float fast_sr2_v010(float *X, float *Y, int n, float alpha, float beta) {
    float p = penalty_sr2_v010(alpha, beta);
    float result = 0.0f;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i];
        i++;
    }
    return result + (float)n * p;
}