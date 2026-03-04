typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
} AoS_v014;

double slow_ds4_v014(AoS_v014 *arr, int n) {
    double total_id = 0.0;
    double total_flags = 0.0;
    for (int i = 0; i < n; i++) {
        total_id += (double)arr[i].id;
        total_flags += (double)arr[i].flags;
    }
    return total_id + total_flags;
}