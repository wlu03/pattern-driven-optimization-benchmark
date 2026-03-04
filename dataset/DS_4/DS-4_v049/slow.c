typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v049;

double slow_ds4_v049(AoS_v049 *arr, int n) {
    double total_normal_x = 0.0;
    double total_depth = 0.0;
    double total_x = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_x += (double)arr[i].normal_x;
        total_depth += (double)arr[i].depth;
        total_x += (double)arr[i].x;
        i++;
    }
    return total_normal_x + total_depth + total_x;
}