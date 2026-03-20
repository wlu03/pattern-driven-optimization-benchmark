#ifndef AOS_V006_DEFINED
#define AOS_V006_DEFINED
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
    double _pad[8];
} AoS_v006;
#endif

__attribute__((noinline))
double aos_accumulate_ds4_v006(AoS_v006 *arr, int n) {
    double total_normal_y = 0.0;
    double total_emissive = 0.0;
    double total_normal_x = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_y += arr[i].normal_y;
        total_emissive += arr[i].emissive;
        total_normal_x += arr[i].normal_x;
        i++;
    }
    return total_normal_y + total_emissive + total_normal_x;
}

__attribute__((noinline))
double soa_accumulate_ds4_v006(double *normal_y, double *emissive, double *normal_x, int n) {
    double total_normal_y = 0.0;
    double total_emissive = 0.0;
    double total_normal_x = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_y += normal_y[i];
        total_emissive += emissive[i];
        total_normal_x += normal_x[i];
        i++;
    }
    return total_normal_y + total_emissive + total_normal_x;
}
