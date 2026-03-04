float fast_sr_1_v013(float *A, float *B, int n, float k0) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += sin(A[i]);
        sum_B += sin(B[i]);
    }
    return (k0 * sum_A) + sum_B;
}