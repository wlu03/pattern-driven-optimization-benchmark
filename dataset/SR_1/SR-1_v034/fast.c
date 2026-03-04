float fast_sr_1_v034(float *A, float *B, float *C, float *D, float *E, int rows, int cols, float k0, float k1, float k2, float k3) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    float sum_D = 0.0f;
    float sum_E = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += A[row * cols + col];
        sum_B += B[row * cols + col];
        sum_C += C[row * cols + col];
        sum_D += D[row * cols + col];
        sum_E += E[row * cols + col];
        }
    }
    return (k0 + sum_A) + (k1 + sum_B) + (k2 + sum_C) + (k3 + sum_D) + sum_E;
}