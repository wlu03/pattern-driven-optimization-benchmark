void slow_is1_v027(float *y, float *x, float alpha, int n) {
    for (int i = 0; i < n; i++) {
        y[i] += alpha * x[i];
    }
}