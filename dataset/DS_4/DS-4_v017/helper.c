#ifndef AOS_V017_DEFINED
#define AOS_V017_DEFINED
typedef struct {
    double px;
    double py;
    double pz;
    double pw;
    double nx;
    double ny;
    double nz;
    double nw;
    double tu;
    double tv;
    double cr;
    double cg;
    double cb;
    double ca;
    double bone_w;
    double bone_id;
    double _pad[16];
} AoS_v017;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v017(AoS_v017 *arr, int n) {
    double total_ny = 0.0;
    double total_py = 0.0;
    for (int i = 0; i < n; i++) {
        total_ny += arr[i].ny;
        total_py += arr[i].py;
    }
    return total_ny + total_py;
}

__attribute__((noinline))
double soa_accumulate_ds4_v017(double *ny, double *py, int n) {
    double total_ny = 0.0;
    double total_py = 0.0;
    for (int i = 0; i < n; i++) {
        total_ny += ny[i];
        total_py += py[i];
    }
    return total_ny + total_py;
}
