typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
} AoS_v004;

double slow_ds4_v004(AoS_v004 *arr, int n) {
    double total_weight = 0.0;
    double total_flags = 0.0;
    double total_id = 0.0;
    double total_timestamp = 0.0;
    int i = 0;
    while (i < n) {
        total_weight += (double)arr[i].weight;
        total_flags += (double)arr[i].flags;
        total_id += (double)arr[i].id;
        total_timestamp += (double)arr[i].timestamp;
        i++;
    }
    return total_weight + total_flags + total_id + total_timestamp;
}