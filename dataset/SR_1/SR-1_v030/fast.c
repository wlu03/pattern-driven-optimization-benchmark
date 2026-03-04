double fast_sr_1_v030(double *A, double *B, double *C, double *D, double *E, int n, double k0, double k1) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    double sum_C = 0.0;
    double sum_D = 0.0;
    double sum_E = 0.0;
    int i = 0;
    while (i < n) {
        sum_A *= A[i];
        sum_B *= B[i];
        sum_C *= C[i];
        sum_D *= D[i];
        sum_E *= E[i];
        i++;
    }
    return (k0 - sum_A) * (k1 - sum_B) * sum_C * sum_D * sum_E;
}