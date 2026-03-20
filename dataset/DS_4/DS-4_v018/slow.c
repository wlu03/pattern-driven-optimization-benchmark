#ifndef AOS_V018_DEFINED
#define AOS_V018_DEFINED
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
} AoS_v018;
#endif

double slow_ds4_v018(AoS_v018 *arr, int n) {
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_pz += (double)arr[i].pz;
    }
    return total_pz;
}