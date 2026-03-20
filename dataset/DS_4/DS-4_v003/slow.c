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
    double total_score = 0.0;
    double total_category = 0.0;
    double total_timestamp = 0.0;
    double total_value = 0.0;
    int i = 0;
    while (i < n) {
        total_score += (double)arr[i].score;
        total_category += (double)arr[i].category;
        total_timestamp += (double)arr[i].timestamp;
        total_value += (double)arr[i].value;
        i++;
    }
    return total_score + total_category + total_timestamp + total_value;
}