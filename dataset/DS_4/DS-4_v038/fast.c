double fast_ds4_v038(double *vy, double *z, double *vx, int n) {
    double total_vy = -1e308;
    double total_z = -1e308;
    double total_vx = -1e308;
    int i = 0;
    while (i < n) {
        if (vy[i] > total_vy) total_vy = vy[i];
        if (z[i] > total_z) total_z = z[i];
        if (vx[i] > total_vx) total_vx = vx[i];
        i++;
    }
    return total_vy + total_z + total_vx;
}