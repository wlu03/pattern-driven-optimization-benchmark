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

double aos_accumulate_ds4_v012(AoS_v012 *arr, int n);

double slow_ds4_v012(AoS_v012 *arr, int n) {
    return aos_accumulate_ds4_v012(arr, n);
}