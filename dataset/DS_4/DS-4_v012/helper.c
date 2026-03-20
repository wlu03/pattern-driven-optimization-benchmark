#ifndef AOS_V012_DEFINED
#define AOS_V012_DEFINED
typedef struct {
    double time;
    double x;
    double y;
    double z;
    double energy;
    double channel;
    double quality;
    double amplitude;
    double phase;
    double duration;
    double rate;
    double peak;
    double baseline;
    double snr;
    double trigger;
    double confidence;
    double _pad[8];
} AoS_v012;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v012(AoS_v012 *arr, int n) {
    double total_y = -1e308;
    double total_energy = -1e308;
    int i = 0;
    while (i < n) {
        if (arr[i].y > total_y) total_y = arr[i].y;
        if (arr[i].energy > total_energy) total_energy = arr[i].energy;
        i++;
    }
    return total_y + total_energy;
}

__attribute__((noinline))
double soa_accumulate_ds4_v012(double *y, double *energy, int n) {
    double total_y = -1e308;
    double total_energy = -1e308;
    int i = 0;
    while (i < n) {
        if (y[i] > total_y) total_y = y[i];
        if (energy[i] > total_energy) total_energy = energy[i];
        i++;
    }
    return total_y + total_energy;
}
