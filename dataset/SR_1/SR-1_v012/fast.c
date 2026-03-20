double fast_sr_1_v012(double *A, double *B, int n, double k0) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
    }
    return ((double)n * k0 - sum_A) + sum_B;
}