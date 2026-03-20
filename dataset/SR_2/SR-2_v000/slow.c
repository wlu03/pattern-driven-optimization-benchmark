float slow_sr2_v000(float *X, float *Y, float *Z, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += gamma * Y[i] + beta * Y[i] * Y[i] * Y[i] + beta * X[i] + alpha * Y[i] * Y[i] * Y[i] + gamma;
    
    }
    return result;
}