int slow_sr_1_v039(int *A, int *B, int *C, int rows, int cols, int k0) {
    int total = 0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 * A[row * cols + col]) + B[row * cols + col] + C[row * cols + col];
        }
    }
    return total;
}