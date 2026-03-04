void slow_is1_v016(double *y, double *x, double alpha, int n) {
    for (int i = 0; i < n; i++) {
        y[i] += alpha * x[i];
    }
}