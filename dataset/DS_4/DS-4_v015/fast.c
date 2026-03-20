double fast_ds4_v015(double *b, int n) {
    double total_b = 0.0;
    int i = 0;
    while (i < n) {
        total_b += b[i];
        i++;
    }
    return total_b;
}