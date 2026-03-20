#ifndef AOS_V008_DEFINED
#define AOS_V008_DEFINED
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
} AoS_v008;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v008(AoS_v008 *arr, int n) {
    double total_radiation = 0.0;
    double total_humidity = 0.0;
    double total_signal = 0.0;
    for (int i = 0; i < n; i++) {
        total_radiation += arr[i].radiation;
        total_humidity += arr[i].humidity;
        total_signal += arr[i].signal;
    }
    return total_radiation + total_humidity + total_signal;
}

__attribute__((noinline))
double soa_accumulate_ds4_v008(double *radiation, double *humidity, double *signal, int n) {
    double total_radiation = 0.0;
    double total_humidity = 0.0;
    double total_signal = 0.0;
    for (int i = 0; i < n; i++) {
        total_radiation += radiation[i];
        total_humidity += humidity[i];
        total_signal += signal[i];
    }
    return total_radiation + total_humidity + total_signal;
}
