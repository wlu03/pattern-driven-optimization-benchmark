typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
} AoS_v009;

double slow_ds4_v009(AoS_v009 *arr, int n) {
    double total_wind_dir = 0.0;
    double total_temp = 0.0;
    double total_wind_speed = 0.0;
    double total_light = 0.0;
    for (int i = 0; i < n; i++) {
        total_wind_dir += (double)arr[i].wind_dir;
        total_temp += (double)arr[i].temp;
        total_wind_speed += (double)arr[i].wind_speed;
        total_light += (double)arr[i].light;
    }
    return total_wind_dir + total_temp + total_wind_speed + total_light;
}