typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
} AoS_v008;

double slow_ds4_v008(AoS_v008 *arr, int n) {
    double total_y = 0.0;
    double total_x = 0.0;
    double total_b = 0.0;
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += (double)arr[i].y;
        total_x += (double)arr[i].x;
        total_b += (double)arr[i].b;
        total_g += (double)arr[i].g;
    }
    return total_y + total_x + total_b + total_g;
}