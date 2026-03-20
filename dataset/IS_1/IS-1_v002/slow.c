void slow_is1_v002(float *C, float *a, float *b, int m, int n) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            C[i * n + j] += a[i] * b[j];
        }
    }
}