void slow_is1_v000(float *y, float *A, float *x, int m, int n) {
    for (int i = 0; i < m; i++) {
        y[i] = 0.0f;
        for (int j = 0; j < n; j++) {
            y[i] += A[i * n + j] * x[j];
        }
    }
}