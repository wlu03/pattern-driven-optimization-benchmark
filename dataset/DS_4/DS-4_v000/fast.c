double fast_ds4_v000(double *nz, double *ny, double *py, double *pz, int n) {
    double total_nz = -1e308;
    double total_ny = -1e308;
    double total_py = -1e308;
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if (nz[i] > total_nz) total_nz = nz[i];
        if (ny[i] > total_ny) total_ny = ny[i];
        if (py[i] > total_py) total_py = py[i];
        if (pz[i] > total_pz) total_pz = pz[i];
    }
    return total_nz + total_ny + total_py + total_pz;
}