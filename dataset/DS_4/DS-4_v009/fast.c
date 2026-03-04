double fast_ds4_v009(double *v, double *py, double *nz, int n) {
    double total_v = 0.0;
    double total_py = 0.0;
    double total_nz = 0.0;
    int i = 0;
    while (i < n) {
        total_v += v[i];
        total_py += py[i];
        total_nz += nz[i];
        i++;
    }
    return total_v + total_py + total_nz;
}