float slow_sr_1_v029(float *A, float *B, float *C, float *D, int rows, int cols, float k0, float k1) {
    float total = 0.0f;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 - A[row * cols + col]) + (k1 - B[row * cols + col]) + C[row * cols + col] + D[row * cols + col];
        }
    }
    return total;
}