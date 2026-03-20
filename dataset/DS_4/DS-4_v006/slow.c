#ifndef AOS_V006_DEFINED
#define AOS_V006_DEFINED
typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
} AoS_v006;
#endif

double slow_ds4_v006(AoS_v006 *arr, int n) {
    double total_x = 1e308;
    double total_quality = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].x < total_x) total_x = (double)arr[i].x;
        if ((double)arr[i].quality < total_quality) total_quality = (double)arr[i].quality;
    }
    return total_x + total_quality;
}