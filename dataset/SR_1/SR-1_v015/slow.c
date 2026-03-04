float slow_sr_1_v015(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1) {
    float total = 0.0f;
    for (int i = 0; i < n; i++) {
        total += (k0 * log(A[i])) + (k1 * log(B[i])) + log(C[i]) + log(D[i]) + log(E[i]) + log(F[i]);
    }
    return total;
}