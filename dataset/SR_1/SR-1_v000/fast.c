double fast_sr_1_v000(double *A, double *B, int n, double k0, double k1) {
    double sum_A = 1;
    double sum_B = 1;
    for (int i = 0; i < n; i++) {
        sum_A *= (k0 - A[i]);
        sum_B *= (k1 - B[i]);
    }
    return sum_A * sum_B;
}