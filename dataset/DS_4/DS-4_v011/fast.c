double fast_ds4_v011(double *y, double *vz, double *x, double *vx, int n) {
    double total_y = -1e308;
    double total_vz = -1e308;
    double total_x = -1e308;
    double total_vx = -1e308;
    int i = 0;
    while (i < n) {
        if (y[i] > total_y) total_y = y[i];
        if (vz[i] > total_vz) total_vz = vz[i];
        if (x[i] > total_x) total_x = x[i];
        if (vx[i] > total_vx) total_vx = vx[i];
        i++;
    }
    return total_y + total_vz + total_x + total_vx;
}