typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
} AoS_v035;

double slow_ds4_v035(AoS_v035 *arr, int n) {
    double total_vx = 1e308;
    double total_vz = 1e308;
    double total_vy = 1e308;
    double total_z = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].vx < total_vx) total_vx = (double)arr[i].vx;
        if ((double)arr[i].vz < total_vz) total_vz = (double)arr[i].vz;
        if ((double)arr[i].vy < total_vy) total_vy = (double)arr[i].vy;
        if ((double)arr[i].z < total_z) total_z = (double)arr[i].z;
    }
    return total_vx + total_vz + total_vy + total_z;
}