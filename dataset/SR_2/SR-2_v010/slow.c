float slow_sr2_v010(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += beta * X[i] * X[i] + beta;
    
    }
    return result;
}