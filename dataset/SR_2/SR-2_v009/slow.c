float slow_sr2_v009(float *X, float *Y, float *Z, float *W, int n, float alpha) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha + alpha * Z[i] * Z[i] * Z[i] + alpha * W[i] * W[i] * W[i] + alpha * Z[i] + alpha;
        i++;
    }
    return result;
}