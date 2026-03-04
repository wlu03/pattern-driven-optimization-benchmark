double fast_ds4_v012(double *px, double *ny, double *pz, int n) {
    double total_px = -1e308;
    double total_ny = -1e308;
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if (px[i] > total_px) total_px = px[i];
        if (ny[i] > total_ny) total_ny = ny[i];
        if (pz[i] > total_pz) total_pz = pz[i];
    }
    return total_px + total_ny + total_pz;
}