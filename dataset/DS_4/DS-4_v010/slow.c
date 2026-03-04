typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v010;

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_r = 1e308;
    double total_b = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].r < total_r) total_r = (double)arr[i].r;
        if ((double)arr[i].b < total_b) total_b = (double)arr[i].b;
    }
    return total_r + total_b;
}