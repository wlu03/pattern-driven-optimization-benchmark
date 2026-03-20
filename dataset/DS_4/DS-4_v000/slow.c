typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
} AoS_v000;

double slow_ds4_v000(AoS_v000 *arr, int n) {
    double total_nz = -1e308;
    double total_ny = -1e308;
    double total_py = -1e308;
    double total_pz = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].nz > total_nz) total_nz = (double)arr[i].nz;
        if ((double)arr[i].ny > total_ny) total_ny = (double)arr[i].ny;
        if ((double)arr[i].py > total_py) total_py = (double)arr[i].py;
        if ((double)arr[i].pz > total_pz) total_pz = (double)arr[i].pz;
    }
    return total_nz + total_ny + total_py + total_pz;
}