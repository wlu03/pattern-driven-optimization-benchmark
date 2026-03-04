float fast_sr_1_v016(float *A, float *B, float *C, float *D, float *E, float *F, int rows, int cols, float k0, float k1, float k2) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    float sum_F = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += sqrt(A[row * cols + col]);
        sum_B += sqrt(B[row * cols + col]);
        sum_C += sqrt(C[row * cols + col]);
        sum_D += sqrt(D[row * cols + col]);
        sum_E += sqrt(E[row * cols + col]);
        sum_F += sqrt(F[row * cols + col]);
        }
    }
    return (k0 + sum_A) + (k1 + sum_B) + (k2 + sum_C) + sum_D + sum_E + sum_F;
}