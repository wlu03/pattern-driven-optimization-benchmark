float fast_sr_1_v026(float *A, float *B, float *C, float *D, int n, float k0) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A += sin(A[i]);
        sum_B += sin(B[i]);
        sum_C += sin(C[i]);
        sum_D += sin(D[i]);
    }
    return (k0 + sum_A) + sum_B + sum_C + sum_D;
}