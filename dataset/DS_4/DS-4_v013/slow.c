#ifndef AOS_V013_DEFINED
#define AOS_V013_DEFINED
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v013;
#endif

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_px = 0.0;
    double total_u = 0.0;
    double total_pz = 0.0;
    double total_nz = 0.0;
    for (int i = 0; i < n; i++) {
        total_px += (double)arr[i].px;
        total_u += (double)arr[i].u;
        total_pz += (double)arr[i].pz;
        total_nz += (double)arr[i].nz;
    }
    return total_px + total_u + total_pz + total_nz;
}