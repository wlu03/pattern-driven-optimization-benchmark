#ifndef AOS_V005_DEFINED
#define AOS_V005_DEFINED
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
    double _pad[24];
} AoS_v005;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v005(AoS_v005 *arr, int n) {
    double total_depth = 0.0;
    double total_opacity = 0.0;
    for (int i = 0; i < n; i++) {
        total_depth += arr[i].depth;
        total_opacity += arr[i].opacity;
    }
    return total_depth + total_opacity;
}

__attribute__((noinline))
double soa_accumulate_ds4_v005(double *depth, double *opacity, int n) {
    double total_depth = 0.0;
    double total_opacity = 0.0;
    for (int i = 0; i < n; i++) {
        total_depth += depth[i];
        total_opacity += opacity[i];
    }
    return total_depth + total_opacity;
}
