#ifndef AOS_V000_DEFINED
#define AOS_V000_DEFINED
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
} AoS_v000;
#endif

double slow_ds4_v000(AoS_v000 *arr, int n) {
    double total_vx = 0.0;
    for (int i = 0; i < n; i++) {
        total_vx += (double)arr[i].vx;
    }
    return total_vx;
}