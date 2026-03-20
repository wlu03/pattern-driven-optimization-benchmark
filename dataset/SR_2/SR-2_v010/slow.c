float penalty_sr2_v010(float a, float b);

float slow_sr2_v010(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0.0f;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i] + penalty_sr2_v010(alpha, beta);
        i++;
    }
    return result;
}