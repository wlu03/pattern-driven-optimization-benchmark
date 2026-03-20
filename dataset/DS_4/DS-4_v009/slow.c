typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v009;

double slow_ds4_v009(AoS_v009 *arr, int n) {
    double total_r = 0.0;
    for (int i = 0; i < n; i++) {
        total_r += (double)arr[i].r;
    }
    return total_r;
}