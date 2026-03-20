float fast_sr_1_v002(float *A, float *B, float *C, int n, float k0) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
    }
    return (k0 * sum_A) + sum_B + sum_C;
}