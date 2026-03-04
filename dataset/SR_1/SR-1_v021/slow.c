float slow_sr_1_v021(float *A, float *B, float *C, float *D, int n, float k0, float k1, float k2, float k3) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 * sin(A[i])) + (k1 * sin(B[i])) + (k2 * sin(C[i])) + (k3 * sin(D[i]));
    }
    return total;
}