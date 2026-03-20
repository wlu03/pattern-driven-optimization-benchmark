typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v004;

double slow_ds4_v004(AoS_v004 *arr, int n) {
    double total_weight = 0.0;
    double total_rank = 0.0;
    for (int i = 0; i < n; i++) {
        total_weight += (double)arr[i].weight;
        total_rank += (double)arr[i].rank;
    }
    return total_weight + total_rank;
}