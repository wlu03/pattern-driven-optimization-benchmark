double fast_comp_v112(double *mass, int n) {
    double total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}