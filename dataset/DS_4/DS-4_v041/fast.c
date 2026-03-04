double fast_ds4_v041(double *y, double *vy, double *vx, double *vz, int n) {
    double total_y = -1e308;
    double total_vy = -1e308;
    double total_vx = -1e308;
    double total_vz = -1e308;
    int i = 0;
    while (i < n) {
        if (y[i] > total_y) total_y = y[i];
        if (vy[i] > total_vy) total_vy = vy[i];
        if (vx[i] > total_vx) total_vx = vx[i];
        if (vz[i] > total_vz) total_vz = vz[i];
        i++;
    }
    return total_y + total_vy + total_vx + total_vz;
}