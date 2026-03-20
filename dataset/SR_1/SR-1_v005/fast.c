double fast_sr_1_v005(double *A, double *B, int rows, int cols, double k0, double k1, double k2, double k3) {
    double sum_A = 1;
    double sum_B = 1;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A *= (k0 + A[row * cols + col]);
        sum_B *= (k1 + B[row * cols + col]);
        }
    }
    return sum_A * sum_B;
}