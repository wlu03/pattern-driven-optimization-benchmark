typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
} AoS_v026;

double slow_ds4_v026(AoS_v026 *arr, int n) {
    double total_z = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].z < total_z) total_z = (double)arr[i].z;
        i++;
    }
    return total_z;
}