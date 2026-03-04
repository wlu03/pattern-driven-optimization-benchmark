double fast_ds4_v018(double *px, double *pz, double *v, double *nx, int n) {
    double total_px = 1e308;
    double total_pz = 1e308;
    double total_v = 1e308;
    double total_nx = 1e308;
    for (int i = 0; i < n; i++) {
        if (px[i] < total_px) total_px = px[i];
        if (pz[i] < total_pz) total_pz = pz[i];
        if (v[i] < total_v) total_v = v[i];
        if (nx[i] < total_nx) total_nx = nx[i];
    }
    return total_px + total_pz + total_v + total_nx;
}