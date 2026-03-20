float fast_sr_1_v011(float *A, float *B, int rows, int cols, float k0) {
    float sum_A = 0.0f;
    float sum_B = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += A[row * cols + col];
        sum_B += B[row * cols + col];
        }
    }
    return (k0 * sum_A) + sum_B;
}