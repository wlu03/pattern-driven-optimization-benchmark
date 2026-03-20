float penalty_sr2_v019(float a, float b);

float slow_sr2_v019(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0.0f;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i] + penalty_sr2_v019(alpha, beta);
    }
    return result;
}