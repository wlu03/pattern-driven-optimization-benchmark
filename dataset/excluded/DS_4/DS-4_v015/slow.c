#ifndef AOS_V015_DEFINED
#define AOS_V015_DEFINED
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
    double _pad[16];
} AoS_v015;
#endif

double aos_accumulate_ds4_v015(AoS_v015 *arr, int n);

double slow_ds4_v015(AoS_v015 *arr, int n) {
    return aos_accumulate_ds4_v015(arr, n);
}