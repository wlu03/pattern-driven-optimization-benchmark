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

__attribute__((noinline))
double aos_accumulate_ds4_v010(AoS_v010 *arr, int n) {
    double total_potential = 0.0;
    double total_kinetic = 0.0;
    int i = 0;
    while (i < n) {
        total_potential += arr[i].potential;
        total_kinetic += arr[i].kinetic;
        i++;
    }
    return total_potential + total_kinetic;
}

__attribute__((noinline))
double soa_accumulate_ds4_v010(double *potential, double *kinetic, int n) {
    double total_potential = 0.0;
    double total_kinetic = 0.0;
    int i = 0;
    while (i < n) {
        total_potential += potential[i];
        total_kinetic += kinetic[i];
        i++;
    }
    return total_potential + total_kinetic;
}
