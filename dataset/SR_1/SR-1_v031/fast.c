double fast_sr_1_v031(double *A, double *B, int n, double k0, double k1, double k2) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
    }
    return (k0 - sum_A) + (k1 - sum_B);
}