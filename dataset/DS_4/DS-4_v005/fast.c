double fast_ds4_v005(double *wind_dir, int n) {
    double total_wind_dir = 1e308;
    for (int i = 0; i < n; i++) {
        if (wind_dir[i] < total_wind_dir) total_wind_dir = wind_dir[i];
    }
    return total_wind_dir;
}