float slow_sr2_v001(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * Z[i] * Z[i] * Z[i] + alpha * X[i] * X[i] * X[i] + beta * X[i] + beta * X[i];
        i++;
    }
    return result;
}