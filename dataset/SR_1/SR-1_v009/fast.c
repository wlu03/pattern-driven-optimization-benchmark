double fast_sr_1_v009(double *A, double *B, double *C, double *D, int n, double k0) {
    double sum_A = 0.0;
    double sum_B = 0.0;
    double sum_C = 0.0;
    double sum_D = 0.0;
    for (int i = 0; i < n; i++) {
        sum_A += cos(A[i]);
        sum_B += cos(B[i]);
        sum_C += cos(C[i]);
        sum_D += cos(D[i]);
    }
    return ((double)n * k0 + sum_A) + sum_B + sum_C + sum_D;
}