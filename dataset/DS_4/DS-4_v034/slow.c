typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
} AoS_v034;

double slow_ds4_v034(AoS_v034 *arr, int n) {
    double total_vx = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].vx > total_vx) total_vx = (double)arr[i].vx;
        i++;
    }
    return total_vx;
}