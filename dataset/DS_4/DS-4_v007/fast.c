double fast_ds4_v007(double *pz, double *ny, double *v, double *u, int n) {
    double total_pz = 1e308;
    double total_ny = 1e308;
    double total_v = 1e308;
    double total_u = 1e308;
    for (int i = 0; i < n; i++) {
        if (pz[i] < total_pz) total_pz = pz[i];
        if (ny[i] < total_ny) total_ny = ny[i];
        if (v[i] < total_v) total_v = v[i];
        if (u[i] < total_u) total_u = u[i];
    }
    return total_pz + total_ny + total_v + total_u;
}