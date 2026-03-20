float penalty_sr2_v008(float a, float b);

float slow_sr2_v008(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float result = 0.0f;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Z[i] + penalty_sr2_v008(alpha, beta);
        i++;
    }
    return result;
}