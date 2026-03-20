void slow_is1_v018(double *C, double *a, double *b, int m, int n) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            C[i * n + j] += a[i] * b[j];
        }
    }
}