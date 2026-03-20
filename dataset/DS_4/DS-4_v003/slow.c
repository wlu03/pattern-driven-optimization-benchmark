#ifndef AOS_V003_DEFINED
#define AOS_V003_DEFINED
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
#endif

double slow_ds4_v003(AoS_v003 *arr, int n) {
    double total_category = -1e308;
    double total_flags = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].category > total_category) total_category = (double)arr[i].category;
        if ((double)arr[i].flags > total_flags) total_flags = (double)arr[i].flags;
        i++;
    }
    return total_category + total_flags;
}