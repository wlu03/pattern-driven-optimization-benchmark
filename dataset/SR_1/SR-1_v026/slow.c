float slow_sr_1_v026(float *A, float *B, float *C, float *D, int n, float k0) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 + sin(A[i])) + sin(B[i]) + sin(C[i]) + sin(D[i]);
    }
    return total;
}