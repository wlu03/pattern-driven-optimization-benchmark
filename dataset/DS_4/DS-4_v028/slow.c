typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
} AoS_v028;

double slow_ds4_v028(AoS_v028 *arr, int n) {
    double total_charge = 0.0;
    double total_z = 0.0;
    int i = 0;
    while (i < n) {
        total_charge += (double)arr[i].charge;
        total_z += (double)arr[i].z;
        i++;
    }
    return total_charge + total_z;
}