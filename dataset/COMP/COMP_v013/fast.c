double fast_comp_v013(double *mass, int n) {
    // Fix DS-4: SoA layout, Fix CF-2: Remove redundant check
    double total = 0.0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}