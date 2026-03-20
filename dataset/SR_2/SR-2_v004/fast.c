float penalty_sr2_v004(float a, float b);

float fast_sr2_v004(float *X, float *Y, int n, float alpha, float beta) {
    float p = penalty_sr2_v004(alpha, beta);
    float result = 0.0f;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i];
    }
    return result + (float)n * p;
}