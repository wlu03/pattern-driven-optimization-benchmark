typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
} AoS_v011;

double slow_ds4_v011(AoS_v011 *arr, int n) {
    double total_light = 1e308;
    double total_humidity = 1e308;
    double total_noise = 1e308;
    double total_pressure = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].light < total_light) total_light = (double)arr[i].light;
        if ((double)arr[i].humidity < total_humidity) total_humidity = (double)arr[i].humidity;
        if ((double)arr[i].noise < total_noise) total_noise = (double)arr[i].noise;
        if ((double)arr[i].pressure < total_pressure) total_pressure = (double)arr[i].pressure;
    }
    return total_light + total_humidity + total_noise + total_pressure;
}