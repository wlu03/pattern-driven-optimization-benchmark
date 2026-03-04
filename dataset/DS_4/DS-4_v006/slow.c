typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
} AoS_v006;

double slow_ds4_v006(AoS_v006 *arr, int n) {
    double total_wind_speed = 0.0;
    double total_wind_dir = 0.0;
    double total_light = 0.0;
    double total_pressure = 0.0;
    int i = 0;
    while (i < n) {
        total_wind_speed += (double)arr[i].wind_speed;
        total_wind_dir += (double)arr[i].wind_dir;
        total_light += (double)arr[i].light;
        total_pressure += (double)arr[i].pressure;
        i++;
    }
    return total_wind_speed + total_wind_dir + total_light + total_pressure;
}