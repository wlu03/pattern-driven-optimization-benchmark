#ifndef AOS_V011_DEFINED
#define AOS_V011_DEFINED
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
} AoS_v011;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v011(AoS_v011 *arr, int n) {
    double total_diffuse = 0.0;
    double total_depth = 0.0;
    for (int i = 0; i < n; i++) {
        total_diffuse += arr[i].diffuse;
        total_depth += arr[i].depth;
    }
    return total_diffuse + total_depth;
}

__attribute__((noinline))
double soa_accumulate_ds4_v011(double *diffuse, double *depth, int n) {
    double total_diffuse = 0.0;
    double total_depth = 0.0;
    for (int i = 0; i < n; i++) {
        total_diffuse += diffuse[i];
        total_depth += depth[i];
    }
    return total_diffuse + total_depth;
}
