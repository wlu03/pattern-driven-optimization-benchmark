typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v001;

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_score = 0.0;
    double total_value = 0.0;
    int i = 0;
    while (i < n) {
        total_score += (double)arr[i].score;
        total_value += (double)arr[i].value;
        i++;
    }
    return total_score + total_value;
}