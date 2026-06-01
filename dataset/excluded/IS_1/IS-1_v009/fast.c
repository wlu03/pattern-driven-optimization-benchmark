void fast_is1_v009(float *y, float *A, float *x, int m, int n) {
    for (int i = 0; i < m; i++) {
        y[i] = 0.0f;
        for (int j = 0; j < n; j++) {
            if (A[i * n + j] == 0.0f) continue;
            y[i] += A[i * n + j] * x[j];
        }
    }
}