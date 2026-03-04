typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
} AoS_v024;

double slow_ds4_v024(AoS_v024 *arr, int n) {
    double total_y = -1e308;
    double total_amplitude = -1e308;
    double total_channel = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].amplitude > total_amplitude) total_amplitude = (double)arr[i].amplitude;
        if ((double)arr[i].channel > total_channel) total_channel = (double)arr[i].channel;
    }
    return total_y + total_amplitude + total_channel;
}