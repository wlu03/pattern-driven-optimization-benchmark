typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
} AoS_v019;

double slow_ds4_v019(AoS_v019 *arr, int n) {
    double total_value = 0.0;
    double total_weight = 0.0;
    double total_flags = 0.0;
    double total_id = 0.0;
    for (int i = 0; i < n; i++) {
        total_value += (double)arr[i].value;
        total_weight += (double)arr[i].weight;
        total_flags += (double)arr[i].flags;
        total_id += (double)arr[i].id;
    }
    return total_value + total_weight + total_flags + total_id;
}