float slow_sr_1_v038(float *A, float *B, float *C, float *D, int n, float k0, float k1) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 - A[i]) + (k1 - B[i]) + C[i] + D[i];
    }
    return total;
}