float slow_sr_1_v042(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2, float k3) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 * cos(A[i])) + (k1 * cos(B[i])) + (k2 * cos(C[i])) + (k3 * cos(D[i])) + cos(E[i]) + cos(F[i]);
    }
    return total;
}