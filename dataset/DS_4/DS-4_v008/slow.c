typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v008;

double slow_ds4_v008(AoS_v008 *arr, int n) {
    double total_quality = 0.0;
    for (int i = 0; i < n; i++) {
        total_quality += (double)arr[i].quality;
    }
    return total_quality;
}