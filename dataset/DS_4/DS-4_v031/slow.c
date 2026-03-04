typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v031;

double slow_ds4_v031(AoS_v031 *arr, int n) {
    double total_quality = 1e308;
    double total_y = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].quality < total_quality) total_quality = (double)arr[i].quality;
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
    }
    return total_quality + total_y;
}