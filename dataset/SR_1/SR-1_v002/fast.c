double fast_sr_1_v002(double *A, double *B, double *C, double *D, double *E, double *F, int rows, int cols, double k0, double k1, double k2, double k3) {
    double sum_A = 1;
    double sum_B = 1;
    double sum_C = 1;
    double sum_D = 1;
    double sum_E = 1;
    double sum_F = 1;
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < cols; col++) {
        sum_A *= (k0 - A[row * cols + col]);
        sum_B *= (k1 - B[row * cols + col]);
        sum_C *= (k2 - C[row * cols + col]);
        sum_D *= (k3 - D[row * cols + col]);
        sum_E *= E[row * cols + col];
        sum_F *= F[row * cols + col];
        }
    }
    return sum_A * sum_B * sum_C * sum_D * sum_E * sum_F;
}