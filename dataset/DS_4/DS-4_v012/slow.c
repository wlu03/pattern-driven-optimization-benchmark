#ifndef AOS_V012_DEFINED
#define AOS_V012_DEFINED
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
} AoS_v012;
#endif

double slow_ds4_v012(AoS_v012 *arr, int n) {
    double total_charge = -1e308;
    double total_x = -1e308;
    double total_mass = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].charge > total_charge) total_charge = (double)arr[i].charge;
        if ((double)arr[i].x > total_x) total_x = (double)arr[i].x;
        if ((double)arr[i].mass > total_mass) total_mass = (double)arr[i].mass;
    }
    return total_charge + total_x + total_mass;
}