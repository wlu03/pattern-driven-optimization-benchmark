float slow_sr_1_v010(float *A, float *B, int n, float k0, float k1, float k2, float k3) {
    float total = 1;
    for (int i = 0; i < n; i++) {
        total *= (k0 * A[i]) * (k1 * B[i]);
    }
    return total;
}