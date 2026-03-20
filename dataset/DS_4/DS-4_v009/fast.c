double fast_ds4_v009(double *r, int n) {
    double total_r = 0.0;
    for (int i = 0; i < n; i++) {
        total_r += r[i];
    }
    return total_r;
}