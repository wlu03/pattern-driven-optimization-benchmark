#ifndef AOS_V010_DEFINED
#define AOS_V010_DEFINED
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
    double _pad[8];
} AoS_v010;
#endif

double aos_accumulate_ds4_v010(AoS_v010 *arr, int n);

double slow_ds4_v010(AoS_v010 *arr, int n) {
    return aos_accumulate_ds4_v010(arr, n);
}