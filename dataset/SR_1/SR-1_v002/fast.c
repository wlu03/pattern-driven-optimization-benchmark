float fast_sr_1_v002(float *A, float *B, float *C, float *D, float *E, float *F, int n, float k0, float k1, float k2) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A *= A[i];
        sum_B *= B[i];
        sum_C *= C[i];
        sum_D *= D[i];
        sum_E *= E[i];
        sum_F *= F[i];
    }
    return (k0 - sum_A) * (k1 - sum_B) * (k2 - sum_C) * sum_D * sum_E * sum_F;
}