typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v005;

double slow_ds4_v005(AoS_v005 *arr, int n) {
    double total_id = -1e308;
    double total_rank = -1e308;
    double total_value = -1e308;
    double total_category = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].id > total_id) total_id = (double)arr[i].id;
        if ((double)arr[i].rank > total_rank) total_rank = (double)arr[i].rank;
        if ((double)arr[i].value > total_value) total_value = (double)arr[i].value;
        if ((double)arr[i].category > total_category) total_category = (double)arr[i].category;
    }
    return total_id + total_rank + total_value + total_category;
}