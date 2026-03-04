double fast_ds4_v034(double *vx, int n) {
    double total_vx = -1e308;
    int i = 0;
    while (i < n) {
        if (vx[i] > total_vx) total_vx = vx[i];
        i++;
    }
    return total_vx;
}