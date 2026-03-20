#ifndef AOS_V004_DEFINED
#define AOS_V004_DEFINED
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
    double fx;
    double fy;
    double fz;
    double potential;
    double kinetic;
    double radius;
    double spin;
    double lifetime;
    double _pad[24];
} AoS_v004;
#endif

double aos_accumulate_ds4_v004(AoS_v004 *arr, int n);

double slow_ds4_v004(AoS_v004 *arr, int n) {
    return aos_accumulate_ds4_v004(arr, n);
}