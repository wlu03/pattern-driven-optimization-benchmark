#ifndef AOS_V009_DEFINED
#define AOS_V009_DEFINED
typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
} AoS_v009;
#endif

double slow_ds4_v009(AoS_v009 *arr, int n) {
    double total_humidity = 0.0;
    double total_light = 0.0;
    double total_noise = 0.0;
    double total_wind_dir = 0.0;
    for (int i = 0; i < n; i++) {
        total_humidity += (double)arr[i].humidity;
        total_light += (double)arr[i].light;
        total_noise += (double)arr[i].noise;
        total_wind_dir += (double)arr[i].wind_dir;
    }
    return total_humidity + total_light + total_noise + total_wind_dir;
}