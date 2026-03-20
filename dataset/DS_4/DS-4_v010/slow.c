typedef struct {
    float px;
    float py;
    float pz;
    float nx;
    float ny;
    float nz;
    float u;
    float v;
} AoS_v010;

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_ny = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].ny > total_ny) total_ny = (double)arr[i].ny;
        i++;
    }
    return total_ny;
}