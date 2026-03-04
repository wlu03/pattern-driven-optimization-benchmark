float fast_sr_1_v020(float *A, float *B, float *C, int n, float k0, float k1) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_A *= cos(A[i]);
        sum_B *= cos(B[i]);
        sum_C *= cos(C[i]);
    }
    return (k0 * sum_A) * (k1 * sum_B) * sum_C;
}