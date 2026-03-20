typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v012;

double slow_ds4_v012(AoS_v012 *arr, int n) {
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_g += (double)arr[i].g;
    }
    return total_g;
}