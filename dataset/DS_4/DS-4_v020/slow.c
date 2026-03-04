typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v020;

double slow_ds4_v020(AoS_v020 *arr, int n) {
    double total_px = 1e308;
    double total_py = 1e308;
    double total_pz = 1e308;
    double total_nz = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].px < total_px) total_px = (double)arr[i].px;
        if ((double)arr[i].py < total_py) total_py = (double)arr[i].py;
        if ((double)arr[i].pz < total_pz) total_pz = (double)arr[i].pz;
        if ((double)arr[i].nz < total_nz) total_nz = (double)arr[i].nz;
    }
    return total_px + total_py + total_pz + total_nz;
}