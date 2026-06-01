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

__attribute__((noinline))
double aos_accumulate_ds4_v015(AoS_v015 *arr, int n) {
    double total_pm10 = 0.0;
    double total_humidity = 0.0;
    double total_signal = 0.0;
    for (int i = 0; i < n; i++) {
        total_pm10 += arr[i].pm10;
        total_humidity += arr[i].humidity;
        total_signal += arr[i].signal;
    }
    return total_pm10 + total_humidity + total_signal;
}

__attribute__((noinline))
double soa_accumulate_ds4_v015(double *pm10, double *humidity, double *signal, int n) {
    double total_pm10 = 0.0;
    double total_humidity = 0.0;
    double total_signal = 0.0;
    for (int i = 0; i < n; i++) {
        total_pm10 += pm10[i];
        total_humidity += humidity[i];
        total_signal += signal[i];
    }
    return total_pm10 + total_humidity + total_signal;
}
