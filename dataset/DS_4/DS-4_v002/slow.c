typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
    double amplitude;
    float phase;
} AoS_v002;

double slow_ds4_v002(AoS_v002 *arr, int n) {
    double total_x = 0.0;
    double total_time = 0.0;
    int i = 0;
    while (i < n) {
        total_x += (double)arr[i].x;
        total_time += (double)arr[i].time;
        i++;
    }
    return total_x + total_time;
}