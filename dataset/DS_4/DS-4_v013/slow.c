typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v013;

double slow_ds4_v013(AoS_v013 *arr, int n) {
    double total_b = 0.0;
    double total_g = 0.0;
    double total_normal_x = 0.0;
    for (int i = 0; i < n; i++) {
        total_b += (double)arr[i].b;
        total_g += (double)arr[i].g;
        total_normal_x += (double)arr[i].normal_x;
    }
    return total_b + total_g + total_normal_x;
}