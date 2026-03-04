double fast_ds4_v028(double *charge, double *z, int n) {
    double total_charge = 0.0;
    double total_z = 0.0;
    int i = 0;
    while (i < n) {
        total_charge += charge[i];
        total_z += z[i];
        i++;
    }
    return total_charge + total_z;
}