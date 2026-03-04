typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v018;

double slow_ds4_v018(AoS_v018 *arr, int n) {
    double total_px = 1e308;
    double total_pz = 1e308;
    double total_v = 1e308;
    double total_nx = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].px < total_px) total_px = (double)arr[i].px;
        if ((double)arr[i].pz < total_pz) total_pz = (double)arr[i].pz;
        if ((double)arr[i].v < total_v) total_v = (double)arr[i].v;
        if ((double)arr[i].nx < total_nx) total_nx = (double)arr[i].nx;
    }
    return total_px + total_pz + total_v + total_nx;
}