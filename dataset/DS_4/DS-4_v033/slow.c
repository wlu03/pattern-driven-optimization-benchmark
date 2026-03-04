typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v033;

double slow_ds4_v033(AoS_v033 *arr, int n) {
    double total_x = 0.0;
    int i = 0;
    while (i < n) {
        total_x += (double)arr[i].x;
        i++;
    }
    return total_x;
}