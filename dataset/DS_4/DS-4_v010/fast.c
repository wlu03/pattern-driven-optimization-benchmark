double fast_ds4_v010(double *py, int n) {
    double total_py = -1e308;
    for (int i = 0; i < n; i++) {
        if (py[i] > total_py) total_py = py[i];
    }
    return total_py;
}