double fast_ds4_v016(double *ny, double *pz, int n) {
    double total_ny = -1e308;
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if (ny[i] > total_ny) total_ny = ny[i];
        if (pz[i] > total_pz) total_pz = pz[i];
    }
    return total_ny + total_pz;
}