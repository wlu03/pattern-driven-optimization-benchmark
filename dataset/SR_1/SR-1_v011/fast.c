float fast_sr_1_v011(float *A, float *B, float *C, float *D, float *E, int n, float k0, float k1, float k2) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    int i = 0;
    while (i < n) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
        sum_D += D[i];
        sum_E += E[i];
        i++;
    }
    return (k0 + sum_A) + (k1 + sum_B) + (k2 + sum_C) + sum_D + sum_E;
}