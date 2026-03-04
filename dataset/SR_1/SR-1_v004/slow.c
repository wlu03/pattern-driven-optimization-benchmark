float slow_sr_1_v004(float *A, float *B, float *C, float *D, int rows, int cols, float k0, float k1, float k2, float k3) {
    float total = 1;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total *= (k0 * A[row * cols + col]) * (k1 * B[row * cols + col]) * (k2 * C[row * cols + col]) * (k3 * D[row * cols + col]);
        }
    }
    return total;
}