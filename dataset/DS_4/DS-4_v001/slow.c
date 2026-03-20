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

double aos_accumulate_ds4_v001(AoS_v001 *arr, int n);

double slow_ds4_v001(AoS_v001 *arr, int n) {
    return aos_accumulate_ds4_v001(arr, n);
}