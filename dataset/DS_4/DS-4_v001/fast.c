double fast_ds4_v001(double *nx, double *ny, double *pz, double *py, int n) {
    double total_nx = 1e308;
    double total_ny = 1e308;
    double total_pz = 1e308;
    double total_py = 1e308;
    int i = 0;
    while (i < n) {
        if (nx[i] < total_nx) total_nx = nx[i];
        if (ny[i] < total_ny) total_ny = ny[i];
        if (pz[i] < total_pz) total_pz = pz[i];
        if (py[i] < total_py) total_py = py[i];
        i++;
    }
    return total_nx + total_ny + total_pz + total_py;
}