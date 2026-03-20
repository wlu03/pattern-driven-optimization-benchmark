#ifndef AOS_V016_DEFINED
#define AOS_V016_DEFINED
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
} AoS_v016;
#endif

double slow_ds4_v016(AoS_v016 *arr, int n) {
    double total_ny = -1e308;
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].ny > total_ny) total_ny = (double)arr[i].ny;
        if ((double)arr[i].pz > total_pz) total_pz = (double)arr[i].pz;
    }
    return total_ny + total_pz;
}