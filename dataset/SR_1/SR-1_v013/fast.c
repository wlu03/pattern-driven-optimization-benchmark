float fast_sr_1_v013(float *A, float *B, float *C, float *D, float *E, float *F, int rows, int cols, float k0, float k1) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += log(A[row * cols + col]);
        sum_B += log(B[row * cols + col]);
        sum_C += log(C[row * cols + col]);
        sum_D += log(D[row * cols + col]);
        sum_E += log(E[row * cols + col]);
        sum_F += log(F[row * cols + col]);
        }
    }
    return (k0 * sum_A) + (k1 * sum_B) + sum_C + sum_D + sum_E + sum_F;
}