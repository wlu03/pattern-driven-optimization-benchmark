#ifndef AOS_V004_DEFINED
#define AOS_V004_DEFINED
typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
} AoS_v004;
#endif

double slow_ds4_v004(AoS_v004 *arr, int n) {
    double total_pressure = 1e308;
    double total_temp = 1e308;
    double total_light = 1e308;
    double total_humidity = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].pressure < total_pressure) total_pressure = (double)arr[i].pressure;
        if ((double)arr[i].temp < total_temp) total_temp = (double)arr[i].temp;
        if ((double)arr[i].light < total_light) total_light = (double)arr[i].light;
        if ((double)arr[i].humidity < total_humidity) total_humidity = (double)arr[i].humidity;
        i++;
    }
    return total_pressure + total_temp + total_light + total_humidity;
}