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

__attribute__((noinline))
double aos_accumulate_ds4_v004(AoS_v004 *arr, int n) {
    double total_fy = 0.0;
    double total_potential = 0.0;
    for (int i = 0; i < n; i++) {
        total_fy += arr[i].fy;
        total_potential += arr[i].potential;
    }
    return total_fy + total_potential;
}

__attribute__((noinline))
double soa_accumulate_ds4_v004(double *fy, double *potential, int n) {
    double total_fy = 0.0;
    double total_potential = 0.0;
    for (int i = 0; i < n; i++) {
        total_fy += fy[i];
        total_potential += potential[i];
    }
    return total_fy + total_potential;
}
