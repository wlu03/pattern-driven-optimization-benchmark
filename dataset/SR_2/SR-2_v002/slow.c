float slow_sr2_v002(float *X, float *Y, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * X[i] * X[i] * X[i] + beta * X[i] + beta * X[i] + gamma * X[i] * X[i];
        i++;
    }
    return result;
}