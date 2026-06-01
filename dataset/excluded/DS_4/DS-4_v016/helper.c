#ifndef AOS_V016_DEFINED
#define AOS_V016_DEFINED
typedef struct {
    double id;
    double timestamp;
    double value;
    double weight;
    double category;
    double flags;
    double score;
    double rank;
    double lat;
    double lon;
    double elevation;
    double accuracy;
    double speed;
    double heading;
    double age;
    double priority;
    double _pad[8];
} AoS_v016;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v016(AoS_v016 *arr, int n) {
    double total_age = -1e308;
    double total_rank = -1e308;
    double total_timestamp = -1e308;
    for (int i = 0; i < n; i++) {
        if (arr[i].age > total_age) total_age = arr[i].age;
        if (arr[i].rank > total_rank) total_rank = arr[i].rank;
        if (arr[i].timestamp > total_timestamp) total_timestamp = arr[i].timestamp;
    }
    return total_age + total_rank + total_timestamp;
}

__attribute__((noinline))
double soa_accumulate_ds4_v016(double *age, double *rank, double *timestamp, int n) {
    double total_age = -1e308;
    double total_rank = -1e308;
    double total_timestamp = -1e308;
    for (int i = 0; i < n; i++) {
        if (age[i] > total_age) total_age = age[i];
        if (rank[i] > total_rank) total_rank = rank[i];
        if (timestamp[i] > total_timestamp) total_timestamp = timestamp[i];
    }
    return total_age + total_rank + total_timestamp;
}
