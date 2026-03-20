double fast_ds4_v013(double *px, double *u, double *pz, double *nz, int n) {
    double total_px = 0.0;
    double total_u = 0.0;
    double total_pz = 0.0;
    double total_nz = 0.0;
    for (int i = 0; i < n; i++) {
        total_px += px[i];
        total_u += u[i];
        total_pz += pz[i];
        total_nz += nz[i];
    }
    return total_px + total_u + total_pz + total_nz;
}