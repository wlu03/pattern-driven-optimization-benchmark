typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
} AoS_v014;

double slow_ds4_v014(AoS_v014 *arr, int n) {
    double total_id = -1e308;
    double total_timestamp = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].id > total_id) total_id = (double)arr[i].id;
        if ((double)arr[i].timestamp > total_timestamp) total_timestamp = (double)arr[i].timestamp;
        i++;
    }
    return total_id + total_timestamp;
}