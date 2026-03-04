float slow_sr_1_v020(float *A, float *B, float *C, int n, float k0, float k1) {
    float total = 1;
    for (int i = 0; i < n; i++) {
        total *= (k0 * cos(A[i])) * (k1 * cos(B[i])) * cos(C[i]);
    }
    return total;
}