double fast_ds4_v036(double *vy, double *mass, double *x, int n) {
    double total_vy = -1e308;
    double total_mass = -1e308;
    double total_x = -1e308;
    for (int i = 0; i < n; i++) {
        if (vy[i] > total_vy) total_vy = vy[i];
        if (mass[i] > total_mass) total_mass = mass[i];
        if (x[i] > total_x) total_x = x[i];
    }
    return total_vy + total_mass + total_x;
}