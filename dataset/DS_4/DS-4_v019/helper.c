#ifndef AOS_V019_DEFINED
#define AOS_V019_DEFINED
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
} AoS_v019;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v019(AoS_v019 *arr, int n) {
    double total_y = 0.0;
    double total_g = 0.0;
    int i = 0;
    while (i < n) {
        total_y += arr[i].y;
        total_g += arr[i].g;
        i++;
    }
    return total_y + total_g;
}

__attribute__((noinline))
double soa_accumulate_ds4_v019(double *y, double *g, int n) {
    double total_y = 0.0;
    double total_g = 0.0;
    int i = 0;
    while (i < n) {
        total_y += y[i];
        total_g += g[i];
        i++;
    }
    return total_y + total_g;
}
