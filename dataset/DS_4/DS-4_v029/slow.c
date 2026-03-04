typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
    float co2;
} AoS_v029;

double slow_ds4_v029(AoS_v029 *arr, int n) {
    double total_pressure = -1e308;
    double total_wind_dir = -1e308;
    double total_co2 = -1e308;
    double total_noise = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pressure > total_pressure) total_pressure = (double)arr[i].pressure;
        if ((double)arr[i].wind_dir > total_wind_dir) total_wind_dir = (double)arr[i].wind_dir;
        if ((double)arr[i].co2 > total_co2) total_co2 = (double)arr[i].co2;
        if ((double)arr[i].noise > total_noise) total_noise = (double)arr[i].noise;
    }
    return total_pressure + total_wind_dir + total_co2 + total_noise;
}