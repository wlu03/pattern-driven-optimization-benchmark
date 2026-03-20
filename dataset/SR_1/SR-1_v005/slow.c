float slow_sr_1_v005(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2, float k3) {
    float total = 0.0f;
    int i = 0;
    while (i < n) {
        total += (k0 - exp(A[i])) + (k1 - exp(B[i])) + (k2 - exp(C[i])) + (k3 - exp(D[i])) + exp(E[i]) + exp(F[i]);
        i++;
    }
    return total;
}