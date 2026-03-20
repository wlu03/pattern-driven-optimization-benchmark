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

double aos_accumulate_ds4_v005(AoS_v005 *arr, int n);

double slow_ds4_v005(AoS_v005 *arr, int n) {
    return aos_accumulate_ds4_v005(arr, n);
}