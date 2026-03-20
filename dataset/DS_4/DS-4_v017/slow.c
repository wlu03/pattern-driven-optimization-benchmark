#ifndef AOS_V017_DEFINED
#define AOS_V017_DEFINED
typedef struct {
    float temp;
    float humidity;
    double pressure;
    float wind_speed;
    float wind_dir;
    int light;
    int noise;
    float co2;
} AoS_v017;
#endif

double slow_ds4_v017(AoS_v017 *arr, int n) {
    double total_light = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].light > total_light) total_light = (double)arr[i].light;
        i++;
    }
    return total_light;
}