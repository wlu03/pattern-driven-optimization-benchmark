float slow_sr_1_v002(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2) {
    float total = 1;
    for (int i = 0; i < n; i++) {
        total *= (k0 - A[i]) * (k1 - B[i]) * (k2 - C[i]) * D[i] * E[i] * F[i];
    }
    return total;
}