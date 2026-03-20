typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
} AoS_v005;

double slow_ds4_v005(AoS_v005 *arr, int n) {
    double total_wind_dir = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].wind_dir < total_wind_dir) total_wind_dir = (double)arr[i].wind_dir;
    }
    return total_wind_dir;
}