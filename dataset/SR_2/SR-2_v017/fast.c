float penalty_sr2_v017(float a, float b);

float fast_sr2_v017(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float p = penalty_sr2_v017(alpha, beta);
    float result = 0.0f;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Z[i];
    }
    return result + (float)n * p;
}