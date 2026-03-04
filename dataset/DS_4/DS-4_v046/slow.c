typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
} AoS_v046;

double slow_ds4_v046(AoS_v046 *arr, int n) {
    double total_pz = 0.0;
    for (int i = 0; i < n; i++) {
        total_pz += (double)arr[i].pz;
    }
    return total_pz;
}