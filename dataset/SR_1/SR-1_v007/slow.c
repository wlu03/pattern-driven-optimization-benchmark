float slow_sr_1_v007(float *A, float *B, int n, float k0) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 - A[i]) + B[i];
    }
    return total;
}