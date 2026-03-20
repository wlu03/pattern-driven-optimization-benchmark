#ifndef AOS_V001_DEFINED
#define AOS_V001_DEFINED
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
} AoS_v001;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v001(AoS_v001 *arr, int n) {
    double total_rate = 0.0;
    double total_confidence = 0.0;
    double total_amplitude = 0.0;
    int i = 0;
    while (i < n) {
        total_rate += arr[i].rate;
        total_confidence += arr[i].confidence;
        total_amplitude += arr[i].amplitude;
        i++;
    }
    return total_rate + total_confidence + total_amplitude;
}

__attribute__((noinline))
double soa_accumulate_ds4_v001(double *rate, double *confidence, double *amplitude, int n) {
    double total_rate = 0.0;
    double total_confidence = 0.0;
    double total_amplitude = 0.0;
    int i = 0;
    while (i < n) {
        total_rate += rate[i];
        total_confidence += confidence[i];
        total_amplitude += amplitude[i];
        i++;
    }
    return total_rate + total_confidence + total_amplitude;
}
