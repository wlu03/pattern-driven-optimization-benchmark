typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
} AoS_v038;

double slow_ds4_v038(AoS_v038 *arr, int n) {
    double total_vy = -1e308;
    double total_z = -1e308;
    double total_vx = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].vy > total_vy) total_vy = (double)arr[i].vy;
        if ((double)arr[i].z > total_z) total_z = (double)arr[i].z;
        if ((double)arr[i].vx > total_vx) total_vx = (double)arr[i].vx;
        i++;
    }
    return total_vy + total_z + total_vx;
}