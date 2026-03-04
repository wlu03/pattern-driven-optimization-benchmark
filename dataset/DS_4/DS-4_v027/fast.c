double fast_ds4_v027(double *energy, double *x, double *channel, int n) {
    double total_energy = 0.0;
    double total_x = 0.0;
    double total_channel = 0.0;
    for (int i = 0; i < n; i++) {
        total_energy += energy[i];
        total_x += x[i];
        total_channel += channel[i];
    }
    return total_energy + total_x + total_channel;
}