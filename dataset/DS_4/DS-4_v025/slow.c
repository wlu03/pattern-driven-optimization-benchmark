typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v025;

double slow_ds4_v025(AoS_v025 *arr, int n) {
    double total_u = -1e308;
    double total_py = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].u > total_u) total_u = (double)arr[i].u;
        if ((double)arr[i].py > total_py) total_py = (double)arr[i].py;
        i++;
    }
    return total_u + total_py;
}