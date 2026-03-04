typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v037;

double slow_ds4_v037(AoS_v037 *arr, int n) {
    double total_x = 0.0;
    double total_time = 0.0;
    double total_energy = 0.0;
    for (int i = 0; i < n; i++) {
        total_x += (double)arr[i].x;
        total_time += (double)arr[i].time;
        total_energy += (double)arr[i].energy;
    }
    return total_x + total_time + total_energy;
}