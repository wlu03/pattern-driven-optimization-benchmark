double fast_ds4_v009(double *humidity, double *light, double *noise, double *wind_dir, int n) {
    double total_humidity = 0.0;
    double total_light = 0.0;
    double total_noise = 0.0;
    double total_wind_dir = 0.0;
    for (int i = 0; i < n; i++) {
        total_humidity += humidity[i];
        total_light += light[i];
        total_noise += noise[i];
        total_wind_dir += wind_dir[i];
    }
    return total_humidity + total_light + total_noise + total_wind_dir;
}