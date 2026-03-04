typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v000;

double slow_ds4_v000(AoS_v000 *arr, int n) {
    double total_flags = 1e308;
    double total_value = 1e308;
    double total_weight = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].flags < total_flags) total_flags = (double)arr[i].flags;
        if ((double)arr[i].value < total_value) total_value = (double)arr[i].value;
        if ((double)arr[i].weight < total_weight) total_weight = (double)arr[i].weight;
    }
    return total_flags + total_value + total_weight;
}