double fast_ds4_v020(double *px, double *py, double *pz, double *nz, int n) {
    double total_px = 1e308;
    double total_py = 1e308;
    double total_pz = 1e308;
    double total_nz = 1e308;
    for (int i = 0; i < n; i++) {
        if (px[i] < total_px) total_px = px[i];
        if (py[i] < total_py) total_py = py[i];
        if (pz[i] < total_pz) total_pz = pz[i];
        if (nz[i] < total_nz) total_nz = nz[i];
    }
    return total_px + total_py + total_pz + total_nz;
}