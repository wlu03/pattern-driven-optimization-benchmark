int fast_comp_v063(int *mass, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}