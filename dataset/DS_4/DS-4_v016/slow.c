typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v016;

double slow_ds4_v016(AoS_v016 *arr, int n) {
    double total_nz = 0.0;
    double total_pz = 0.0;
    double total_u = 0.0;
    double total_px = 0.0;
    int i = 0;
    while (i < n) {
        total_nz += (double)arr[i].nz;
        total_pz += (double)arr[i].pz;
        total_u += (double)arr[i].u;
        total_px += (double)arr[i].px;
        i++;
    }
    return total_nz + total_pz + total_u + total_px;
}