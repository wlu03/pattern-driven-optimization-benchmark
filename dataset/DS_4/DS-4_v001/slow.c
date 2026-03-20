#ifndef AOS_V001_DEFINED
#define AOS_V001_DEFINED
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v001;
#endif

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_ny = -1e308;
    double total_nz = -1e308;
    double total_u = -1e308;
    double total_nx = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].ny > total_ny) total_ny = (double)arr[i].ny;
        if ((double)arr[i].nz > total_nz) total_nz = (double)arr[i].nz;
        if ((double)arr[i].u > total_u) total_u = (double)arr[i].u;
        if ((double)arr[i].nx > total_nx) total_nx = (double)arr[i].nx;
    }
    return total_ny + total_nz + total_u + total_nx;
}