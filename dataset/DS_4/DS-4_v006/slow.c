typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
} AoS_v006;

double slow_ds4_v006(AoS_v006 *arr, int n) {
    double total_a = -1e308;
    double total_b = -1e308;
    double total_x = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].a > total_a) total_a = (double)arr[i].a;
        if ((double)arr[i].b > total_b) total_b = (double)arr[i].b;
        if ((double)arr[i].x > total_x) total_x = (double)arr[i].x;
        i++;
    }
    return total_a + total_b + total_x;
}