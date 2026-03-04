float fast_sr_1_v038(float *A, float *B, float *C, float *D, int n, float k0, float k1) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
        sum_D += D[i];
    }
    return (k0 - sum_A) + (k1 - sum_B) + sum_C + sum_D;
}