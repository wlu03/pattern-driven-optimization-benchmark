float fast_sr_1_v006(float *A, float *B, float *C, int rows, int cols, float k0, float k1) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    float sum_C = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += A[row * cols + col];
        sum_B += B[row * cols + col];
        sum_C += C[row * cols + col];
        }
    }
    return ((float)rows * cols * k0 - sum_A) + ((float)rows * cols * k1 - sum_B) + sum_C;
}