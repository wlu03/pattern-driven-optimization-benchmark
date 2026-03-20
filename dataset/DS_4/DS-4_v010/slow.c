#ifndef AOS_V010_DEFINED
#define AOS_V010_DEFINED
typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v010;
#endif

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_u = 0.0;
    double total_ny = 0.0;
    double total_pz = 0.0;
    int i = 0;
    while (i < n) {
        total_u += (double)arr[i].u;
        total_ny += (double)arr[i].ny;
        total_pz += (double)arr[i].pz;
        i++;
    }
    return total_u + total_ny + total_pz;
}