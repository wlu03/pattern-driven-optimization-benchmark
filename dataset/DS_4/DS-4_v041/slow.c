typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
} AoS_v041;

double slow_ds4_v041(AoS_v041 *arr, int n) {
    double total_y = -1e308;
    double total_vy = -1e308;
    double total_vx = -1e308;
    double total_vz = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].y > total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].vy > total_vy) total_vy = (double)arr[i].vy;
        if ((double)arr[i].vx > total_vx) total_vx = (double)arr[i].vx;
        if ((double)arr[i].vz > total_vz) total_vz = (double)arr[i].vz;
        i++;
    }
    return total_y + total_vy + total_vx + total_vz;
}