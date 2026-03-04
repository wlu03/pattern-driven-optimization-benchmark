float fast_sr_1_v042(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2, float k3) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += cos(A[i]);
        sum_B += cos(B[i]);
        sum_C += cos(C[i]);
        sum_D += cos(D[i]);
        sum_E += cos(E[i]);
        sum_F += cos(F[i]);
    }
    return (k0 * sum_A) + (k1 * sum_B) + (k2 * sum_C) + (k3 * sum_D) + sum_E + sum_F;
}