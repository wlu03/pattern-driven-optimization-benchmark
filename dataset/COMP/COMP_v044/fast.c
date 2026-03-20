double fast_comp_v044(double *mass, int n) {
    double total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}