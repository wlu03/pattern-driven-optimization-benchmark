float slow_sr2_v003(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * Z[i] * Z[i] + gamma * Z[i] * Z[i] * Z[i] + beta * Y[i] * Y[i] * Y[i] + alpha + beta;
        i++;
    }
    return result;
}