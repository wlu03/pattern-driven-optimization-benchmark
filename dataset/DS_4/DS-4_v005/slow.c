typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
    float phase;
} AoS_v005;

double slow_ds4_v005(AoS_v005 *arr, int n) {
    double total_phase = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].phase < total_phase) total_phase = (double)arr[i].phase;
    }
    return total_phase;
}