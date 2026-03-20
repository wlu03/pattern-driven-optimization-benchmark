float fast_sr_1_v007(float *A, float *B, int n, float k0) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
    }
    return ((float)n * k0 - sum_A) + sum_B;
}