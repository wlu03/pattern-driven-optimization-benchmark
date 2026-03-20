double fast_ds4_v010(double *u, double *ny, double *pz, int n) {
    double total_u = 0.0;
    double total_ny = 0.0;
    double total_pz = 0.0;
    int i = 0;
    while (i < n) {
        total_u += u[i];
        total_ny += ny[i];
        total_pz += pz[i];
        i++;
    }
    return total_u + total_ny + total_pz;
}