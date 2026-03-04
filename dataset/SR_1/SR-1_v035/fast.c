double fast_sr_1_v035(double *A, double *B, double *C, double *D, double *E, double *F, int rows, int cols, double k0, double k1, double k2, double k3) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    double sum_C = 0.0;
    double sum_D = 0.0;
    double sum_E = 0.0;
    double sum_F = 0.0;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A *= A[row * cols + col];
        sum_B *= B[row * cols + col];
        sum_C *= C[row * cols + col];
        sum_D *= D[row * cols + col];
        sum_E *= E[row * cols + col];
        sum_F *= F[row * cols + col];
        }
    }
    return (k0 * sum_A) * (k1 * sum_B) * (k2 * sum_C) * (k3 * sum_D) * sum_E * sum_F;
}