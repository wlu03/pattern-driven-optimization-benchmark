float slow_sr2_v007(float *X, float *Y, int n, float alpha) {
    float result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * Y[i] * Y[i] * Y[i] + alpha * Y[i] * Y[i] + alpha + alpha + alpha * Y[i];
    
    }
    return result;
}