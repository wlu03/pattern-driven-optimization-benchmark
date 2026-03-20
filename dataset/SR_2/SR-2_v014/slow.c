float slow_sr2_v014(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta, float gamma) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + gamma;
    
    }
    return result;
}