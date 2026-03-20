typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
} AoS_v013;

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_u = 0.0;
    int i = 0;
    while (i < n) {
        total_u += (double)arr[i].u;
        i++;
    }
    return total_u;
}