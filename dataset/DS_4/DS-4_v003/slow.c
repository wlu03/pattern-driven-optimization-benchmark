typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v003;

double slow_ds4_v003(AoS_v003 *arr, int n) {
    double total_rank = -1e308;
    double total_timestamp = -1e308;
    double total_weight = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].rank > total_rank) total_rank = (double)arr[i].rank;
        if ((double)arr[i].timestamp > total_timestamp) total_timestamp = (double)arr[i].timestamp;
        if ((double)arr[i].weight > total_weight) total_weight = (double)arr[i].weight;
        i++;
    }
    return total_rank + total_timestamp + total_weight;
}