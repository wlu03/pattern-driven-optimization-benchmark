float slow_sr2_v009(float *X, float *Y, float *Z, int n, float alpha) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha + alpha + alpha * X[i] * X[i] * X[i];
        i++;
    }
    return result;
}