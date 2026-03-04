float slow_sr_1_v013(float *A, float *B, int n, float k0) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 * sin(A[i])) + sin(B[i]);
    }
    return total;
}