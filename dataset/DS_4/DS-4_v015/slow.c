typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
} AoS_v015;

double slow_ds4_v015(AoS_v015 *arr, int n) {
    double total_y = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
        i++;
    }
    return total_y;
}