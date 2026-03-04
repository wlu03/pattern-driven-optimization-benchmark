double fast_ds4_v023(double *noise, double *light, double *wind_dir, int n) {
    double total_noise = 1e308;
    double total_light = 1e308;
    double total_wind_dir = 1e308;
    for (int i = 0; i < n; i++) {
        if (noise[i] < total_noise) total_noise = noise[i];
        if (light[i] < total_light) total_light = light[i];
        if (wind_dir[i] < total_wind_dir) total_wind_dir = wind_dir[i];
    }
    return total_noise + total_light + total_wind_dir;
}