float slow_sr2_v003(float *X, float *Y, float *Z, int n, float alpha, float beta) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] * X[i] + alpha * Y[i] + beta;
        i++;
    }
    return result;
}