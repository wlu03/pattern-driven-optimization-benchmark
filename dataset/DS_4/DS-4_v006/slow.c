typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v006;

double slow_ds4_v006(AoS_v006 *arr, int n) {
    double total_nz = 0.0;
    int i = 0;
    while (i < n) {
        total_nz += (double)arr[i].nz;
        i++;
    }
    return total_nz;
}