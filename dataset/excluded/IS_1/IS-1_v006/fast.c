void fast_is1_v006(double *y, double *A, double *x, int m, int n) {
    for (int i = 0; i < m; i++) {
        y[i] = 0.0;
        for (int j = 0; j < n; j++) {
            if (A[i * n + j] == 0.0) continue;
            y[i] += A[i * n + j] * x[j];
        }
    }
}