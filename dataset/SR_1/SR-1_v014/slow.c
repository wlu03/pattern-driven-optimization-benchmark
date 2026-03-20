int slow_sr_1_v014(int *A, int *B, int *C, int rows, int cols, int k0, int k1, int k2, int k3) {
    int total = 0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 * A[row * cols + col]) + (k1 * B[row * cols + col]) + (k2 * C[row * cols + col]);
        }
    }
    return total;
}