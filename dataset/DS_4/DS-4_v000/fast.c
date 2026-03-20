double fast_ds4_v000(double *vx, int n) {
    double total_vx = 0.0;
    for (int i = 0; i < n; i++) {
        total_vx += vx[i];
    }
    return total_vx;
}