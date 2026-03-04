typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
} AoS_v002;

double slow_ds4_v002(AoS_v002 *arr, int n) {
    double total_value = 0.0;
    double total_category = 0.0;
    double total_flags = 0.0;
    double total_timestamp = 0.0;
    for (int i = 0; i < n; i++) {
        total_value += (double)arr[i].value;
        total_category += (double)arr[i].category;
        total_flags += (double)arr[i].flags;
        total_timestamp += (double)arr[i].timestamp;
    }
    return total_value + total_category + total_flags + total_timestamp;
}