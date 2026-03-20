double fast_sr_1_v002(double *A, double *B, double *C, double *D, int n, double k0, double k1, double k2, double k3) {
    double sum_A = 1;
    double sum_B = 1;
    double sum_C = 1;
    double sum_D = 1;
    for (int i = 0; i < n; i++) {
        sum_A *= (k0 - A[i]);
        sum_B *= (k1 - B[i]);
        sum_C *= (k2 - C[i]);
        sum_D *= (k3 - D[i]);
    }
    return sum_A * sum_B * sum_C * sum_D;
}