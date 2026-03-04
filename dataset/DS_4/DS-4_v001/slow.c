typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
} AoS_v001;

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_nx = 1e308;
    double total_ny = 1e308;
    double total_pz = 1e308;
    double total_py = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].nx < total_nx) total_nx = (double)arr[i].nx;
        if ((double)arr[i].ny < total_ny) total_ny = (double)arr[i].ny;
        if ((double)arr[i].pz < total_pz) total_pz = (double)arr[i].pz;
        if ((double)arr[i].py < total_py) total_py = (double)arr[i].py;
        i++;
    }
    return total_nx + total_ny + total_pz + total_py;
}