typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v011;

double slow_ds4_v011(AoS_v011 *arr, int n) {
    double total_py = -1e308;
    double total_pz = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].py > total_py) total_py = (double)arr[i].py;
        if ((double)arr[i].pz > total_pz) total_pz = (double)arr[i].pz;
        i++;
    }
    return total_py + total_pz;
}