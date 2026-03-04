typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
} AoS_v047;

double slow_ds4_v047(AoS_v047 *arr, int n) {
    double total_px = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].px > total_px) total_px = (double)arr[i].px;
        i++;
    }
    return total_px;
}