typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
    float co2;
} AoS_v002;

double slow_ds4_v002(AoS_v002 *arr, int n) {
    double total_temp = 0.0;
    double total_humidity = 0.0;
    double total_light = 0.0;
    for (int i = 0; i < n; i++) {
        total_temp += (double)arr[i].temp;
        total_humidity += (double)arr[i].humidity;
        total_light += (double)arr[i].light;
    }
    return total_temp + total_humidity + total_light;
}