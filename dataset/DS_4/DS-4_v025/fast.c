double fast_ds4_v025(double *u, double *py, int n) {
    double total_u = -1e308;
    double total_py = -1e308;
    int i = 0;
    while (i < n) {
        if (u[i] > total_u) total_u = u[i];
        if (py[i] > total_py) total_py = py[i];
        i++;
    }
    return total_u + total_py;
}