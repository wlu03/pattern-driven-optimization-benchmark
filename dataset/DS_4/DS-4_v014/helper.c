#ifndef AOS_V014_DEFINED
#define AOS_V014_DEFINED
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
    double _pad[24];
} AoS_v014;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v014(AoS_v014 *arr, int n) {
    double total_amplitude = -1e308;
    double total_confidence = -1e308;
    for (int i = 0; i < n; i++) {
        if (arr[i].amplitude > total_amplitude) total_amplitude = arr[i].amplitude;
        if (arr[i].confidence > total_confidence) total_confidence = arr[i].confidence;
    }
    return total_amplitude + total_confidence;
}

__attribute__((noinline))
double soa_accumulate_ds4_v014(double *amplitude, double *confidence, int n) {
    double total_amplitude = -1e308;
    double total_confidence = -1e308;
    for (int i = 0; i < n; i++) {
        if (amplitude[i] > total_amplitude) total_amplitude = amplitude[i];
        if (confidence[i] > total_confidence) total_confidence = confidence[i];
    }
    return total_amplitude + total_confidence;
}
