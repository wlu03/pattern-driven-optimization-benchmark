float fast_sr_1_v004(float *A, float *B, float *C, float *D, float *E, int n, float k0) {
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
    return ((float)n * k0 - sum_A) + sum_B + sum_C + sum_D + sum_E;
}