float fast_sr_1_v005(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2, float k3) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    int i = 0;
    while (i < n) {
        sum_A += exp(A[i]);
        sum_B += exp(B[i]);
        sum_C += exp(C[i]);
        sum_D += exp(D[i]);
        sum_E += exp(E[i]);
        sum_F += exp(F[i]);
        i++;
    }
    return ((float)n * k0 - sum_A) + ((float)n * k1 - sum_B) + ((float)n * k2 - sum_C) + ((float)n * k3 - sum_D) + sum_E + sum_F;
}