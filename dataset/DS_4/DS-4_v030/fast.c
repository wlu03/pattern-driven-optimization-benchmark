double fast_ds4_v030(double *u, double *px, double *pz, int n) {
    double total_u = 0.0;
    double total_px = 0.0;
    double total_pz = 0.0;
    int i = 0;
    while (i < n) {
        total_u += u[i];
        total_px += px[i];
        total_pz += pz[i];
        i++;
    }
    return total_u + total_px + total_pz;
}