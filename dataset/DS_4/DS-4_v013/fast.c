double fast_ds4_v013(double *pressure, double *co2, double *wind_speed, int n) {
    double total_pressure = -1e308;
    double total_co2 = -1e308;
    double total_wind_speed = -1e308;
    for (int i = 0; i < n; i++) {
        if (pressure[i] > total_pressure) total_pressure = pressure[i];
        if (co2[i] > total_co2) total_co2 = co2[i];
        if (wind_speed[i] > total_wind_speed) total_wind_speed = wind_speed[i];
    }
    return total_pressure + total_co2 + total_wind_speed;
}