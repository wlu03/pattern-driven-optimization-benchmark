typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v040;

double slow_ds4_v040(AoS_v040 *arr, int n) {
    double total_x = 0.0;
    int i = 0;
    while (i < n) {
        total_x += (double)arr[i].x;
        i++;
    }
    return total_x;
}