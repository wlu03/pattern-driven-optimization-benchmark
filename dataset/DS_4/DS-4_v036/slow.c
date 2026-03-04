typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
} AoS_v036;

double slow_ds4_v036(AoS_v036 *arr, int n) {
    double total_vy = -1e308;
    double total_mass = -1e308;
    double total_x = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].vy > total_vy) total_vy = (double)arr[i].vy;
        if ((double)arr[i].mass > total_mass) total_mass = (double)arr[i].mass;
        if ((double)arr[i].x > total_x) total_x = (double)arr[i].x;
    }
    return total_vy + total_mass + total_x;
}