typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
} AoS_v048;

double slow_ds4_v048(AoS_v048 *arr, int n) {
    double total_y = -1e308;
    double total_x = -1e308;
    double total_vy = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].x > total_x) total_x = (double)arr[i].x;
        if ((double)arr[i].vy > total_vy) total_vy = (double)arr[i].vy;
    }
    return total_y + total_x + total_vy;
}