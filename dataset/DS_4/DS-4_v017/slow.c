typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v017;

double slow_ds4_v017(AoS_v017 *arr, int n) {
    double total_r = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].r < total_r) total_r = (double)arr[i].r;
    }
    return total_r;
}