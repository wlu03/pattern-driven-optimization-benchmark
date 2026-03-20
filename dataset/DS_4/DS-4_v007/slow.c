typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v007;

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_depth = -1e308;
    double total_normal_x = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].depth > total_depth) total_depth = (double)arr[i].depth;
        if ((double)arr[i].normal_x > total_normal_x) total_normal_x = (double)arr[i].normal_x;
    }
    return total_depth + total_normal_x;
}