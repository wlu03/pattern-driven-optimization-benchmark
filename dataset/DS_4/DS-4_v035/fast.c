double fast_ds4_v035(double *vx, double *vz, double *vy, double *z, int n) {
    double total_vx = 1e308;
    double total_vz = 1e308;
    double total_vy = 1e308;
    double total_z = 1e308;
    for (int i = 0; i < n; i++) {
        if (vx[i] < total_vx) total_vx = vx[i];
        if (vz[i] < total_vz) total_vz = vz[i];
        if (vy[i] < total_vy) total_vy = vy[i];
        if (z[i] < total_z) total_z = z[i];
    }
    return total_vx + total_vz + total_vy + total_z;
}