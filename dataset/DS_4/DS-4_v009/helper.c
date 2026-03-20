#ifndef AOS_V009_DEFINED
#define AOS_V009_DEFINED
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
    double _pad[16];
} AoS_v009;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v009(AoS_v009 *arr, int n) {
    double total_channel = -1e308;
    double total_baseline = -1e308;
    double total_z = -1e308;
    for (int i = 0; i < n; i++) {
        if (arr[i].channel > total_channel) total_channel = arr[i].channel;
        if (arr[i].baseline > total_baseline) total_baseline = arr[i].baseline;
        if (arr[i].z > total_z) total_z = arr[i].z;
    }
    return total_channel + total_baseline + total_z;
}

__attribute__((noinline))
double soa_accumulate_ds4_v009(double *channel, double *baseline, double *z, int n) {
    double total_channel = -1e308;
    double total_baseline = -1e308;
    double total_z = -1e308;
    for (int i = 0; i < n; i++) {
        if (channel[i] > total_channel) total_channel = channel[i];
        if (baseline[i] > total_baseline) total_baseline = baseline[i];
        if (z[i] > total_z) total_z = z[i];
    }
    return total_channel + total_baseline + total_z;
}
