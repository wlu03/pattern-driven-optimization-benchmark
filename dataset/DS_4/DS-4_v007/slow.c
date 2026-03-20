typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
} AoS_v007;

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_vy = 0.0;
    double total_y = 0.0;
    for (int i = 0; i < n; i++) {
        total_vy += (double)arr[i].vy;
        total_y += (double)arr[i].y;
    }
    return total_vy + total_y;
}