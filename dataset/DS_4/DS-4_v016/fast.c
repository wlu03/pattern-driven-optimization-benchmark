double fast_ds4_v016(double *nz, double *pz, double *u, double *px, int n) {
    double total_nz = 0.0;
    double total_pz = 0.0;
    double total_u = 0.0;
    double total_px = 0.0;
    int i = 0;
    while (i < n) {
        total_nz += nz[i];
        total_pz += pz[i];
        total_u += u[i];
        total_px += px[i];
        i++;
    }
    return total_nz + total_pz + total_u + total_px;
}