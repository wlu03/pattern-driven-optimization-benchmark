typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v007;

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_pz = 1e308;
    double total_ny = 1e308;
    double total_v = 1e308;
    double total_u = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pz < total_pz) total_pz = (double)arr[i].pz;
        if ((double)arr[i].ny < total_ny) total_ny = (double)arr[i].ny;
        if ((double)arr[i].v < total_v) total_v = (double)arr[i].v;
        if ((double)arr[i].u < total_u) total_u = (double)arr[i].u;
    }
    return total_pz + total_ny + total_v + total_u;
}