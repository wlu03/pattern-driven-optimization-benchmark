float slow_sr2_v007(float *X, float *Y, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += beta + gamma * X[i] * X[i] * X[i] + beta * X[i] * X[i] * X[i] + alpha * Y[i] * Y[i];
    
    }
    return result;
}