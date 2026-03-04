typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v039;

double slow_ds4_v039(AoS_v039 *arr, int n) {
    double total_value = 0.0;
    double total_timestamp = 0.0;
    double total_rank = 0.0;
    double total_weight = 0.0;
    for (int i = 0; i < n; i++) {
        total_value += (double)arr[i].value;
        total_timestamp += (double)arr[i].timestamp;
        total_rank += (double)arr[i].rank;
        total_weight += (double)arr[i].weight;
    }
    return total_value + total_timestamp + total_rank + total_weight;
}