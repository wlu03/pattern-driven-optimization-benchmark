typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
} AoS_v003;

double slow_ds4_v003(AoS_v003 *arr, int n) {
    double total_value = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].value < total_value) total_value = (double)arr[i].value;
    }
    return total_value;
}