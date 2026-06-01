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

double aos_accumulate_ds4_v016(AoS_v016 *arr, int n);

double slow_ds4_v016(AoS_v016 *arr, int n) {
    return aos_accumulate_ds4_v016(arr, n);
}