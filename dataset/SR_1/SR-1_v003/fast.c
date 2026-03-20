double fast_sr_1_v003(double *A, double *B, int n, double k0, double k1) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    int i = 0;
    while (i < n) {
        sum_A += A[i];
        sum_B += B[i];
        i++;
    }
    return ((double)n * k0 - sum_A) + ((double)n * k1 - sum_B);
}