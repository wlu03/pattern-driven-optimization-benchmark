int fast_sr_1_v008(int *A, int *B, int *C, int *D, int *E, int n, int k0, int k1, int k2) {
    int sum_A = 0;
    int sum_B = 0;
    int sum_C = 0;
    int sum_D = 0;
    int sum_E = 0;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
        sum_D += D[i];
        sum_E += E[i];
    }
    return ((int)n * k0 - sum_A) + ((int)n * k1 - sum_B) + ((int)n * k2 - sum_C) + sum_D + sum_E;
}