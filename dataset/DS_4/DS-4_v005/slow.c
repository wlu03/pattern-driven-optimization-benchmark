#ifndef AOS_V005_DEFINED
#define AOS_V005_DEFINED
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
} AoS_v005;
#endif

double slow_ds4_v005(AoS_v005 *arr, int n) {
    double total_y = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += (double)arr[i].y;
    }
    return total_y;
}