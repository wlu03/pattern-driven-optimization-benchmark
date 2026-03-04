double fast_ds4_v006(double *wind_speed, double *wind_dir, double *light, double *pressure, int n) {
    double total_wind_speed = 0.0;
    double total_wind_dir = 0.0;
    double total_light = 0.0;
    double total_pressure = 0.0;
    int i = 0;
    while (i < n) {
        total_wind_speed += wind_speed[i];
        total_wind_dir += wind_dir[i];
        total_light += light[i];
        total_pressure += pressure[i];
        i++;
    }
    return total_wind_speed + total_wind_dir + total_light + total_pressure;
}