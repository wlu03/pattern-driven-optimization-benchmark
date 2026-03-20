typedef struct {
    double time;
    double x;
    double y;
    float energy;
    int channel;
    int quality;
} AoS_v001;

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_channel = 0.0;
    int i = 0;
    while (i < n) {
        total_channel += (double)arr[i].channel;
        i++;
    }
    return total_channel;
}