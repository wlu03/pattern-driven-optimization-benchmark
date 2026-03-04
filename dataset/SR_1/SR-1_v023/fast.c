float fast_sr_1_v023(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2, float k3) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += sin(A[i]);
        sum_B += sin(B[i]);
        sum_C += sin(C[i]);
        sum_D += sin(D[i]);
        sum_E += sin(E[i]);
        sum_F += sin(F[i]);
    }
    return (k0 - sum_A) + (k1 - sum_B) + (k2 - sum_C) + (k3 - sum_D) + sum_E + sum_F;
}