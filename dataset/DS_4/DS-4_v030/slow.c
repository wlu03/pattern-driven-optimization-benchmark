typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v030;

double slow_ds4_v030(AoS_v030 *arr, int n) {
    double total_u = 0.0;
    double total_px = 0.0;
    double total_pz = 0.0;
    int i = 0;
    while (i < n) {
        total_u += (double)arr[i].u;
        total_px += (double)arr[i].px;
        total_pz += (double)arr[i].pz;
        i++;
    }
    return total_u + total_px + total_pz;
}