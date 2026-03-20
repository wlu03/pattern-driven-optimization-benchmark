int fast_sr_1_v011(int *A, int *B, int *C, int *D, int n, int k0, int k1) {
    int sum_A = 0;
    int sum_B = 0;
    int sum_C = 0;
    int sum_D = 0;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
        sum_D += D[i];
    }
    return ((int)n * k0 + sum_A) + ((int)n * k1 + sum_B) + sum_C + sum_D;
}