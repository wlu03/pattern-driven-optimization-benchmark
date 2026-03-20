float slow_sr2_v013(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * Y[i] * Y[i] + alpha * Y[i];
        i++;
    }
    return result;
}