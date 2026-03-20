float slow_sr2_v011(float *X, float *Y, int n, float alpha) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] * X[i] + alpha * X[i] + alpha * Y[i] * Y[i] * Y[i] + alpha;
        i++;
    }
    return result;
}