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

double aos_accumulate_ds4_v011(AoS_v011 *arr, int n);

double slow_ds4_v011(AoS_v011 *arr, int n) {
    return aos_accumulate_ds4_v011(arr, n);
}