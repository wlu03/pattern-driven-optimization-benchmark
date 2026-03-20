int slow_sr_1_v003(int *A, int *B, int *C, int *D, int rows, int cols, int k0, int k1) {
    int total = 0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 + A[row * cols + col]) + (k1 + B[row * cols + col]) + C[row * cols + col] + D[row * cols + col];
        }
    }
    return total;
}