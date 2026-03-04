float fast_sr_1_v015(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += log(A[i]);
        sum_B += log(B[i]);
        sum_C += log(C[i]);
        sum_D += log(D[i]);
        sum_E += log(E[i]);
        sum_F += log(F[i]);
    }
    return (k0 * sum_A) + (k1 * sum_B) + sum_C + sum_D + sum_E + sum_F;
}