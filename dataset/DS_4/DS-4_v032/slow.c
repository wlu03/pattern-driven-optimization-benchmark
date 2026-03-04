typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
    float phase;
} AoS_v032;

double slow_ds4_v032(AoS_v032 *arr, int n) {
    double total_amplitude = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].amplitude < total_amplitude) total_amplitude = (double)arr[i].amplitude;
    }
    return total_amplitude;
}