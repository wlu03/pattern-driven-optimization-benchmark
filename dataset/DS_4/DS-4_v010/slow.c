typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
} AoS_v010;

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_py = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].py > total_py) total_py = (double)arr[i].py;
    }
    return total_py;
}