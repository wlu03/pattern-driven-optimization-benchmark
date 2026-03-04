double fast_ds4_v047(double *px, int n) {
    double total_px = -1e308;
    int i = 0;
    while (i < n) {
        if (px[i] > total_px) total_px = px[i];
        i++;
    }
    return total_px;
}