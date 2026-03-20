double fast_ds4_v002(double *temp, double *humidity, double *light, int n) {
    double total_temp = 0.0;
    double total_humidity = 0.0;
    double total_light = 0.0;
    for (int i = 0; i < n; i++) {
        total_temp += temp[i];
        total_humidity += humidity[i];
        total_light += light[i];
    }
    return total_temp + total_humidity + total_light;
}