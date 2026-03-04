double fast_sr_1_v032(double *A, double *B, double *C, int rows, int cols, double k0, double k1, double k2) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    double sum_C = 0.0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A += log(A[row * cols + col]);
        sum_B += log(B[row * cols + col]);
        sum_C += log(C[row * cols + col]);
        }
    }
    return (k0 + sum_A) + (k1 + sum_B) + (k2 + sum_C);
}