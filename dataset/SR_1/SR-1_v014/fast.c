int fast_sr_1_v014(int *A, int *B, int *C, int n, int k0) {
    int sum_A = 0;
    int sum_B = 0;
    int sum_C = 0;
    for (int i = 0; i < n; i++) {
        sum_A += A[i];
        sum_B += B[i];
        sum_C += C[i];
    }
    return ((int)n * k0 + sum_A) + sum_B + sum_C;
}