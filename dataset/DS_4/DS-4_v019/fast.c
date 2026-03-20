double fast_ds4_v019(double *time, double *amplitude, double *y, double *energy, int n) {
    double total_time = -1e308;
    double total_amplitude = -1e308;
    double total_y = -1e308;
    double total_energy = -1e308;
    for (int i = 0; i < n; i++) {
        if (time[i] > total_time) total_time = time[i];
        if (amplitude[i] > total_amplitude) total_amplitude = amplitude[i];
        if (y[i] > total_y) total_y = y[i];
        if (energy[i] > total_energy) total_energy = energy[i];
    }
    return total_time + total_amplitude + total_y + total_energy;
}