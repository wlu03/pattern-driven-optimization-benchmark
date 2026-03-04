void fast_is1_v021(double *y, double *x, double alpha, int n) {
    if (alpha == 0.0) return;
    for (int i = 0; i < n; i++) {
        if (x[i] == 0.0) continue;
        y[i] += alpha * x[i];
    }
}