float slow_sr2_v006(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * Y[i] * Y[i] * Y[i] + beta * X[i] * X[i] * X[i];
        i++;
    }
    return result;
}