typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
    float co2;
} AoS_v013;

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_pressure = -1e308;
    double total_co2 = -1e308;
    double total_wind_speed = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pressure > total_pressure) total_pressure = (double)arr[i].pressure;
        if ((double)arr[i].co2 > total_co2) total_co2 = (double)arr[i].co2;
        if ((double)arr[i].wind_speed > total_wind_speed) total_wind_speed = (double)arr[i].wind_speed;
    }
    return total_pressure + total_co2 + total_wind_speed;
}