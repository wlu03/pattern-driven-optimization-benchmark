double fast_ds4_v009(double *wind_dir, double *temp, double *wind_speed, double *light, int n) {
    double total_wind_dir = 0.0;
    double total_temp = 0.0;
    double total_wind_speed = 0.0;
    double total_light = 0.0;
    for (int i = 0; i < n; i++) {
        total_wind_dir += wind_dir[i];
        total_temp += temp[i];
        total_wind_speed += wind_speed[i];
        total_light += light[i];
    }
    return total_wind_dir + total_temp + total_wind_speed + total_light;
}