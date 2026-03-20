float slow_sr_1_v003(float *A, float *B, float *C, float *D, float *E, int n, float k0, float k1) {
    float total = 1;
    for (int i = 0; i < n; i++) {
        total *= (k0 * fabs(A[i])) * (k1 * fabs(B[i])) * fabs(C[i]) * fabs(D[i]) * fabs(E[i]);
    }
    return total;
}