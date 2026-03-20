void slow_is1_v005(float *C, float *A, float *B, int m, int k, int n) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            C[i * n + j] = 0.0f;
            for (int p = 0; p < k; p++) {
                C[i * n + j] += A[i * k + p] * B[p * n + j];
            }
        }
    }
}