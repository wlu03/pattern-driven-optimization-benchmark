float slow_sr_1_v027(float *A, float *B, float *C, float *D, int n, float k0, float k1, float k2, float k3) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 - A[i]) + (k1 - B[i]) + (k2 - C[i]) + (k3 - D[i]);
    }
    return total;
}