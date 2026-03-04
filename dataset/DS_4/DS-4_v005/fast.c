double fast_ds4_v005(double *phase, int n) {
    double total_phase = 1e308;
    for (int i = 0; i < n; i++) {
        if (phase[i] < total_phase) total_phase = phase[i];
    }
    return total_phase;
}