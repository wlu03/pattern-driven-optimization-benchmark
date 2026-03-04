typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
} AoS_v042;

double slow_ds4_v042(AoS_v042 *arr, int n) {
    double total_y = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += (double)arr[i].y;
        total_a += (double)arr[i].a;
    }
    return total_y + total_a;
}