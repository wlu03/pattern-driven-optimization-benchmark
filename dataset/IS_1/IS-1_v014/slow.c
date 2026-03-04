void slow_is1_v014(float *y, float *x, float alpha, int n) {
    for (int i = 0; i < n; i++) {
        y[i] += alpha * x[i];
    }
}