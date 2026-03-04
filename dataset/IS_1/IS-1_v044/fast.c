void fast_is1_v044(float *y, float *x, float alpha, int n) {
    if (alpha == 0.0f) return;
    for (int i = 0; i < n; i++) {
        if (x[i] == 0.0f) continue;
        y[i] += alpha * x[i];
    }
}