double fast_sr_1_v044(double *A, double *B, double *C, double *D, int n, double k0, double k1, double k2, double k3) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    double sum_C = 0.0;
    double sum_D = 0.0;
    for (int i = 0; i < n; i++) {
        sum_A *= A[i];
        sum_B *= B[i];
        sum_C *= C[i];
        sum_D *= D[i];
    }
    return (k0 + sum_A) * (k1 + sum_B) * (k2 + sum_C) * (k3 + sum_D);
}