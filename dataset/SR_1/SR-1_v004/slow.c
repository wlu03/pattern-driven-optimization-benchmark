float slow_sr_1_v004(float *A, float *B, int rows, int cols, float k0, float k1, float k2) {
    float total = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 + A[row * cols + col]) + (k1 + B[row * cols + col]);
        }
    }
    return total;
}