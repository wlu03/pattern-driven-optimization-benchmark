double slow_sr_1_v032(double *A, double *B, double *C, int rows, int cols, double k0, double k1, double k2) {
    double total = 0.0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 + log(A[row * cols + col])) + (k1 + log(B[row * cols + col])) + (k2 + log(C[row * cols + col]));
        }
    }
    return total;
}