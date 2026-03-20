#ifndef AOS_V019_DEFINED
#define AOS_V019_DEFINED
typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
} AoS_v019;
#endif

double slow_ds4_v019(AoS_v019 *arr, int n) {
    double total_time = -1e308;
    double total_amplitude = -1e308;
    double total_y = -1e308;
    double total_energy = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].time > total_time) total_time = (double)arr[i].time;
        if ((double)arr[i].amplitude > total_amplitude) total_amplitude = (double)arr[i].amplitude;
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].energy > total_energy) total_energy = (double)arr[i].energy;
    }
    return total_time + total_amplitude + total_y + total_energy;
}