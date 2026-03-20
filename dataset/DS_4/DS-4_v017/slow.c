#ifndef AOS_V017_DEFINED
#define AOS_V017_DEFINED
typedef struct {
    double px;
    double py;
    double pz;
    double pw;
    double nx;
    double ny;
    double nz;
    double nw;
    double tu;
    double tv;
    double cr;
    double cg;
    double cb;
    double ca;
    double bone_w;
    double bone_id;
    double _pad[16];
} AoS_v017;
#endif

double aos_accumulate_ds4_v017(AoS_v017 *arr, int n);

double slow_ds4_v017(AoS_v017 *arr, int n) {
    return aos_accumulate_ds4_v017(arr, n);
}