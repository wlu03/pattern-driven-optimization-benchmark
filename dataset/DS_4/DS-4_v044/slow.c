typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
} AoS_v044;

double slow_ds4_v044(AoS_v044 *arr, int n) {
    double total_light = -1e308;
    double total_wind_dir = -1e308;
    double total_wind_speed = -1e308;
    double total_pressure = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].light > total_light) total_light = (double)arr[i].light;
        if ((double)arr[i].wind_dir > total_wind_dir) total_wind_dir = (double)arr[i].wind_dir;
        if ((double)arr[i].wind_speed > total_wind_speed) total_wind_speed = (double)arr[i].wind_speed;
        if ((double)arr[i].pressure > total_pressure) total_pressure = (double)arr[i].pressure;
        i++;
    }
    return total_light + total_wind_dir + total_wind_speed + total_pressure;
}