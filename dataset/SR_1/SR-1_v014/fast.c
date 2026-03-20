int fast_sr_1_v014(int *A, int *B, int *C, int rows, int cols, int k0, int k1, int k2, int k3) {
    int sum_A = 0;
    int sum_B = 0;
    int sum_C = 0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += A[row * cols + col];
        sum_B += B[row * cols + col];
        sum_C += C[row * cols + col];
        }
    }
    return (k0 * sum_A) + (k1 * sum_B) + (k2 * sum_C);
}