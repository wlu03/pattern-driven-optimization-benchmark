double fast_ds4_v014(double *energy, double *y, int n) {
    double total_energy = -1e308;
    double total_y = -1e308;
    for (int i = 0; i < n; i++) {
        if (energy[i] > total_energy) total_energy = energy[i];
        if (y[i] > total_y) total_y = y[i];
    }
    return total_energy + total_y;
}