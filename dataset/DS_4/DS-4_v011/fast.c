double fast_ds4_v011(double *light, double *humidity, double *noise, double *pressure, int n) {
    double total_light = 1e308;
    double total_humidity = 1e308;
    double total_noise = 1e308;
    double total_pressure = 1e308;
    for (int i = 0; i < n; i++) {
        if (light[i] < total_light) total_light = light[i];
        if (humidity[i] < total_humidity) total_humidity = humidity[i];
        if (noise[i] < total_noise) total_noise = noise[i];
        if (pressure[i] < total_pressure) total_pressure = pressure[i];
    }
    return total_light + total_humidity + total_noise + total_pressure;
}