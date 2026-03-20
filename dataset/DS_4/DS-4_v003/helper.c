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

__attribute__((noinline))
double aos_accumulate_ds4_v003(AoS_v003 *arr, int n) {
    double total_temp = -1e308;
    double total_co2 = -1e308;
    double total_signal = -1e308;
    for (int i = 0; i < n; i++) {
        if (arr[i].temp > total_temp) total_temp = arr[i].temp;
        if (arr[i].co2 > total_co2) total_co2 = arr[i].co2;
        if (arr[i].signal > total_signal) total_signal = arr[i].signal;
    }
    return total_temp + total_co2 + total_signal;
}

__attribute__((noinline))
double soa_accumulate_ds4_v003(double *temp, double *co2, double *signal, int n) {
    double total_temp = -1e308;
    double total_co2 = -1e308;
    double total_signal = -1e308;
    for (int i = 0; i < n; i++) {
        if (temp[i] > total_temp) total_temp = temp[i];
        if (co2[i] > total_co2) total_co2 = co2[i];
        if (signal[i] > total_signal) total_signal = signal[i];
    }
    return total_temp + total_co2 + total_signal;
}
