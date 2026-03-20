double fast_ds4_v001(double *ny, double *nz, double *u, double *nx, int n) {
    double total_ny = -1e308;
    double total_nz = -1e308;
    double total_u = -1e308;
    double total_nx = -1e308;
    for (int i = 0; i < n; i++) {
        if (ny[i] > total_ny) total_ny = ny[i];
        if (nz[i] > total_nz) total_nz = nz[i];
        if (u[i] > total_u) total_u = u[i];
        if (nx[i] > total_nx) total_nx = nx[i];
    }
    return total_ny + total_nz + total_u + total_nx;
}