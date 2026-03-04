typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
} AoS_v043;

double slow_ds4_v043(AoS_v043 *arr, int n) {
    double total_timestamp = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].timestamp > total_timestamp) total_timestamp = (double)arr[i].timestamp;
    }
    return total_timestamp;
}