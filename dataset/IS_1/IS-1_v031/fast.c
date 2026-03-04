void fast_is1_v031(double *C, double *a, double *b, int m, int n) {
    for (int i = 0; i < m; i++) {
        if (a[i] == 0.0) continue;
        for (int j = 0; j < n; j++) {
            if (b[j] == 0.0) continue;
            C[i * n + j] += a[i] * b[j];
        }
    }
}