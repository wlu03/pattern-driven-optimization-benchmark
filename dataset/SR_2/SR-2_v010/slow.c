float slow_sr2_v010(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * Z[i] * Z[i] + gamma * W[i] * W[i] + beta * X[i] * X[i] * X[i];
        i++;
    }
    return result;
}