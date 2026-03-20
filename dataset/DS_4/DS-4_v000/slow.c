typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v000;

double slow_ds4_v000(AoS_v000 *arr, int n) {
    double total_g = 1e308;
    double total_r = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].g < total_g) total_g = (double)arr[i].g;
        if ((double)arr[i].r < total_r) total_r = (double)arr[i].r;
        if ((double)arr[i].x < total_x) total_x = (double)arr[i].x;
    }
    return total_g + total_r + total_x;
}