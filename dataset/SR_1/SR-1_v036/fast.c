int fast_sr_1_v036(int *A, int *B, int *C, int *D, int *E, int rows, int cols, int k0) {
    int sum_A = 0;
    int sum_B = 0;
    int sum_C = 0;
    int sum_D = 0;
    int sum_E = 0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += A[row * cols + col];
        sum_B += B[row * cols + col];
        sum_C += C[row * cols + col];
        sum_D += D[row * cols + col];
        sum_E += E[row * cols + col];
        }
    }
    return (k0 * sum_A) + sum_B + sum_C + sum_D + sum_E;
}