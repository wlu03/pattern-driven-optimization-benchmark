double fast_ds4_v037(double *x, double *time, double *energy, int n) {
    double total_x = 0.0;
    double total_time = 0.0;
    double total_energy = 0.0;
    for (int i = 0; i < n; i++) {
        total_x += x[i];
        total_time += time[i];
        total_energy += energy[i];
    }
    return total_x + total_time + total_energy;
}