double slow_sr_1_v006(double *A, double *B, double *C, double *D, int rows, int cols, double k0) {
    double total = 0.0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 + A[row * cols + col]) + B[row * cols + col] + C[row * cols + col] + D[row * cols + col];
        }
    }
    return total;
}