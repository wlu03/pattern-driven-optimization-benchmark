typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
    float co2;
} AoS_v023;

double slow_ds4_v023(AoS_v023 *arr, int n) {
    double total_noise = 1e308;
    double total_light = 1e308;
    double total_wind_dir = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].noise < total_noise) total_noise = (double)arr[i].noise;
        if ((double)arr[i].light < total_light) total_light = (double)arr[i].light;
        if ((double)arr[i].wind_dir < total_wind_dir) total_wind_dir = (double)arr[i].wind_dir;
    }
    return total_noise + total_light + total_wind_dir;
}