typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v045;

double slow_ds4_v045(AoS_v045 *arr, int n) {
    double total_a = -1e308;
    double total_y = -1e308;
    double total_normal_x = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].a > total_a) total_a = (double)arr[i].a;
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].normal_x > total_normal_x) total_normal_x = (double)arr[i].normal_x;
    }
    return total_a + total_y + total_normal_x;
}