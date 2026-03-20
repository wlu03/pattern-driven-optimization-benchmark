#ifndef AOS_V013_DEFINED
#define AOS_V013_DEFINED
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
} AoS_v013;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v013(AoS_v013 *arr, int n) {
    double total_baseline = 0.0;
    double total_trigger = 0.0;
    double total_peak = 0.0;
    for (int i = 0; i < n; i++) {
        total_baseline += arr[i].baseline;
        total_trigger += arr[i].trigger;
        total_peak += arr[i].peak;
    }
    return total_baseline + total_trigger + total_peak;
}

__attribute__((noinline))
double soa_accumulate_ds4_v013(double *baseline, double *trigger, double *peak, int n) {
    double total_baseline = 0.0;
    double total_trigger = 0.0;
    double total_peak = 0.0;
    for (int i = 0; i < n; i++) {
        total_baseline += baseline[i];
        total_trigger += trigger[i];
        total_peak += peak[i];
    }
    return total_baseline + total_trigger + total_peak;
}
