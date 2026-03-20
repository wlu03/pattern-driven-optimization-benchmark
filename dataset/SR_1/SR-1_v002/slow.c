float slow_sr_1_v002(float *A, float *B, float *C, int n, float k0) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 * A[i]) + B[i] + C[i];
    }
    return total;
}