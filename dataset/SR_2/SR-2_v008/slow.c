float slow_sr2_v008(float *X, float *Y, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + beta + beta * Y[i] + alpha * Y[i] + alpha;
    
    }
    return result;
}