typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
} AoS_v011;

double slow_ds4_v011(AoS_v011 *arr, int n) {
    double total_y = 1e308;
    double total_time = 1e308;
    double total_amplitude = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].time < total_time) total_time = (double)arr[i].time;
        if ((double)arr[i].amplitude < total_amplitude) total_amplitude = (double)arr[i].amplitude;
    }
    return total_y + total_time + total_amplitude;
}