typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v027;

double slow_ds4_v027(AoS_v027 *arr, int n) {
    double total_energy = 0.0;
    double total_x = 0.0;
    double total_channel = 0.0;
    for (int i = 0; i < n; i++) {
        total_energy += (double)arr[i].energy;
        total_x += (double)arr[i].x;
        total_channel += (double)arr[i].channel;
    }
    return total_energy + total_x + total_channel;
}