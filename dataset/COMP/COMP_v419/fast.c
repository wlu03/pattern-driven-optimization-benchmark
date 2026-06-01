float fast_comp_v419(float *mass, int n) {
    float total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}