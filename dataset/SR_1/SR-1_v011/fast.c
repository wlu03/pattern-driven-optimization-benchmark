int fast_sr_1_v011(int *A, int *B, int *C, int n, int k0, int k1, int k2) {
    int sum_A = 0;
    int sum_B = 0;
    int sum_C = 0;
    int i = 0;
    while (i < n) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
        i++;
    }
    return ((int)n * k0 - sum_A) + ((int)n * k1 - sum_B) + ((int)n * k2 - sum_C);
}