#ifndef AOS_V003_DEFINED
#define AOS_V003_DEFINED
typedef struct {
    double temp;
    double humidity;
    double pressure;
    double wind_speed;
    double wind_dir;
    double light;
    double noise;
    double co2;
    double pm25;
    double pm10;
    double ozone;
    double radiation;
    double voltage;
    double current;
    double frequency;
    double signal;
    double _pad[24];
} AoS_v003;
#endif

double aos_accumulate_ds4_v003(AoS_v003 *arr, int n);

double slow_ds4_v003(AoS_v003 *arr, int n) {
    return aos_accumulate_ds4_v003(arr, n);
}