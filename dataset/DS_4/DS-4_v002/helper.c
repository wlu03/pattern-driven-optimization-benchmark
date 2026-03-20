#ifndef AOS_V002_DEFINED
#define AOS_V002_DEFINED
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
    double _pad[8];
} AoS_v002;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v002(AoS_v002 *arr, int n) {
    double total_cb = -1e308;
    double total_cg = -1e308;
    for (int i = 0; i < n; i++) {
        if (arr[i].cb > total_cb) total_cb = arr[i].cb;
        if (arr[i].cg > total_cg) total_cg = arr[i].cg;
    }
    return total_cb + total_cg;
}

__attribute__((noinline))
double soa_accumulate_ds4_v002(double *cb, double *cg, int n) {
    double total_cb = -1e308;
    double total_cg = -1e308;
    for (int i = 0; i < n; i++) {
        if (cb[i] > total_cb) total_cb = cb[i];
        if (cg[i] > total_cg) total_cg = cg[i];
    }
    return total_cb + total_cg;
}
