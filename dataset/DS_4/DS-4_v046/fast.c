double fast_ds4_v046(double *pz, int n) {
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_pz += pz[i];
    }
    return total_pz;
}