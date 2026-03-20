double fast_sr_1_v000(double *A, double *B, double *C, int n, double k0, double k1, double k2) {
    double sum_A = 1;
    double sum_B = 1;
    double sum_C = 1;
    for (int i = 0; i < n; i++) {
        sum_A *= (k0 - A[i]);
        sum_B *= (k1 - B[i]);
        sum_C *= (k2 - C[i]);
    }
    return sum_A * sum_B * sum_C;
}