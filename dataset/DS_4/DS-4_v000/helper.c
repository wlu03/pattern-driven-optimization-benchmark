#ifndef AOS_V000_DEFINED
#define AOS_V000_DEFINED
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
} AoS_v000;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v000(AoS_v000 *arr, int n) {
    double total_pressure = 0.0;
    double total_ozone = 0.0;
    for (int i = 0; i < n; i++) {
        total_pressure += arr[i].pressure;
        total_ozone += arr[i].ozone;
    }
    return total_pressure + total_ozone;
}

__attribute__((noinline))
double soa_accumulate_ds4_v000(double *pressure, double *ozone, int n) {
    double total_pressure = 0.0;
    double total_ozone = 0.0;
    for (int i = 0; i < n; i++) {
        total_pressure += pressure[i];
        total_ozone += ozone[i];
    }
    return total_pressure + total_ozone;
}
