typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v009;

double slow_ds4_v009(AoS_v009 *arr, int n) {
    double total_v = 0.0;
    double total_py = 0.0;
    double total_nz = 0.0;
    int i = 0;
    while (i < n) {
        total_v += (double)arr[i].v;
        total_py += (double)arr[i].py;
        total_nz += (double)arr[i].nz;
        i++;
    }
    return total_v + total_py + total_nz;
}