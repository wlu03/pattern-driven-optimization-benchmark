double fast_ds4_v012(double *charge, double *x, double *mass, int n) {
    double total_charge = -1e308;
    double total_x = -1e308;
    double total_mass = -1e308;
    for (int i = 0; i < n; i++) {
        if (charge[i] > total_charge) total_charge = charge[i];
        if (x[i] > total_x) total_x = x[i];
        if (mass[i] > total_mass) total_mass = mass[i];
    }
    return total_charge + total_x + total_mass;
}