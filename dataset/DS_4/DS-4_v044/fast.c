double fast_ds4_v044(double *light, double *wind_dir, double *wind_speed, double *pressure, int n) {
    double total_light = -1e308;
    double total_wind_dir = -1e308;
    double total_wind_speed = -1e308;
    double total_pressure = -1e308;
    int i = 0;
    while (i < n) {
        if (light[i] > total_light) total_light = light[i];
        if (wind_dir[i] > total_wind_dir) total_wind_dir = wind_dir[i];
        if (wind_speed[i] > total_wind_speed) total_wind_speed = wind_speed[i];
        if (pressure[i] > total_pressure) total_pressure = pressure[i];
        i++;
    }
    return total_light + total_wind_dir + total_wind_speed + total_pressure;
}