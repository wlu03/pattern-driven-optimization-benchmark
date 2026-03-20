#ifndef AOS_V014_DEFINED
#define AOS_V014_DEFINED
typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v014;
#endif

double slow_ds4_v014(AoS_v014 *arr, int n) {
    double total_energy = -1e308;
    double total_y = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].energy > total_energy) total_energy = (double)arr[i].energy;
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
    }
    return total_energy + total_y;
}