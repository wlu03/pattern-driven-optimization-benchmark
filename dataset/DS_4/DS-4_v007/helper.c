#ifndef AOS_V007_DEFINED
#define AOS_V007_DEFINED
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
} AoS_v007;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v007(AoS_v007 *arr, int n) {
    double total_pz = 0.0;
    double total_nw = 0.0;
    for (int i = 0; i < n; i++) {
        total_pz += arr[i].pz;
        total_nw += arr[i].nw;
    }
    return total_pz + total_nw;
}

__attribute__((noinline))
double soa_accumulate_ds4_v007(double *pz, double *nw, int n) {
    double total_pz = 0.0;
    double total_nw = 0.0;
    for (int i = 0; i < n; i++) {
        total_pz += pz[i];
        total_nw += nw[i];
    }
    return total_pz + total_nw;
}
