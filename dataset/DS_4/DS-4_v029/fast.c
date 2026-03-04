double fast_ds4_v029(double *pressure, double *wind_dir, double *co2, double *noise, int n) {
    double total_pressure = -1e308;
    double total_wind_dir = -1e308;
    double total_co2 = -1e308;
    double total_noise = -1e308;
    for (int i = 0; i < n; i++) {
        if (pressure[i] > total_pressure) total_pressure = pressure[i];
        if (wind_dir[i] > total_wind_dir) total_wind_dir = wind_dir[i];
        if (co2[i] > total_co2) total_co2 = co2[i];
        if (noise[i] > total_noise) total_noise = noise[i];
    }
    return total_pressure + total_wind_dir + total_co2 + total_noise;
}