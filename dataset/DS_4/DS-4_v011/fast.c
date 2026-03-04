double fast_ds4_v011(double *py, double *pz, int n) {
    double total_py = -1e308;
    double total_pz = -1e308;
    int i = 0;
    while (i < n) {
        if (py[i] > total_py) total_py = py[i];
        if (pz[i] > total_pz) total_pz = pz[i];
        i++;
    }
    return total_py + total_pz;
}