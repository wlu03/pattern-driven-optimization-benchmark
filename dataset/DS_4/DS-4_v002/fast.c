double fast_ds4_v002(double *x, double *time, int n) {
    double total_x = 0.0;
    double total_time = 0.0;
    int i = 0;
    while (i < n) {
        total_x += x[i];
        total_time += time[i];
        i++;
    }
    return total_x + total_time;
}