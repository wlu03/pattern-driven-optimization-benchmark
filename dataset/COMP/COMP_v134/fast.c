double fast_comp_v134(double *mass, int n) {
    double total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}