double fast_ds4_v022(double *vx, double *vy, double *vz, double *x, int n) {
    double total_vx = -1e308;
    double total_vy = -1e308;
    double total_vz = -1e308;
    double total_x = -1e308;
    for (int i = 0; i < n; i++) {
        if (vx[i] > total_vx) total_vx = vx[i];
        if (vy[i] > total_vy) total_vy = vy[i];
        if (vz[i] > total_vz) total_vz = vz[i];
        if (x[i] > total_x) total_x = x[i];
    }
    return total_vx + total_vy + total_vz + total_x;
}