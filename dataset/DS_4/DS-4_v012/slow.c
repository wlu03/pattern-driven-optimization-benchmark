typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
} AoS_v012;

double slow_ds4_v012(AoS_v012 *arr, int n) {
    double total_px = -1e308;
    double total_ny = -1e308;
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].px > total_px) total_px = (double)arr[i].px;
        if ((double)arr[i].ny > total_ny) total_ny = (double)arr[i].ny;
        if ((double)arr[i].pz > total_pz) total_pz = (double)arr[i].pz;
    }
    return total_px + total_ny + total_pz;
}