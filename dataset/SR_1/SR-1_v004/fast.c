double fast_sr_1_v004(double *A, double *B, int n, double k0, double k1, double k2, double k3) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    for (int i = 0; i < n; i++) {
        sum_A += log(A[i]);
        sum_B += log(B[i]);
    }
    return ((double)n * k0 - sum_A) + ((double)n * k1 - sum_B);
}