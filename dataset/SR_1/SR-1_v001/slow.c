double slow_sr_1_v001(double *A, double *B, double *C, double *D, int rows, int cols, double k0, double k1) {
    double total = 0.0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        total += (k0 * log(A[row * cols + col])) + (k1 * log(B[row * cols + col])) + log(C[row * cols + col]) + log(D[row * cols + col]);
        }
    }
    return total;
}