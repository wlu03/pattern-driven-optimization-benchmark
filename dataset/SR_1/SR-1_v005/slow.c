double slow_sr_1_v005(double *A, double *B, int rows, int cols, double k0, double k1, double k2, double k3) {
    double total = 1;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total *= (k0 + A[row * cols + col]) * (k1 + B[row * cols + col]);
        }
    }
    return total;
}