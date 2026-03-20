#ifndef AOS_V018_DEFINED
#define AOS_V018_DEFINED
typedef struct {
    double r;
    double g;
    double b;
    double a;
    double x;
    double y;
    double depth;
    double normal_x;
    double normal_y;
    double normal_z;
    double u;
    double v;
    double specular;
    double diffuse;
    double emissive;
    double opacity;
    double _pad[16];
} AoS_v018;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v018(AoS_v018 *arr, int n) {
    double total_normal_y = 0.0;
    double total_depth = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_y += arr[i].normal_y;
        total_depth += arr[i].depth;
        i++;
    }
    return total_normal_y + total_depth;
}

__attribute__((noinline))
double soa_accumulate_ds4_v018(double *normal_y, double *depth, int n) {
    double total_normal_y = 0.0;
    double total_depth = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_y += normal_y[i];
        total_depth += depth[i];
        i++;
    }
    return total_normal_y + total_depth;
}
