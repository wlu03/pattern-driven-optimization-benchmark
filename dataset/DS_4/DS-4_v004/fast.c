double fast_ds4_v004(double *pressure, double *temp, double *light, double *humidity, int n) {
    double total_pressure = 1e308;
    double total_temp = 1e308;
    double total_light = 1e308;
    double total_humidity = 1e308;
    int i = 0;
    while (i < n) {
        if (pressure[i] < total_pressure) total_pressure = pressure[i];
        if (temp[i] < total_temp) total_temp = temp[i];
        if (light[i] < total_light) total_light = light[i];
        if (humidity[i] < total_humidity) total_humidity = humidity[i];
        i++;
    }
    return total_pressure + total_temp + total_light + total_humidity;
}