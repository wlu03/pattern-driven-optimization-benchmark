#ifndef AOS_V008_DEFINED
#define AOS_V008_DEFINED
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v008;
#endif

double slow_ds4_v008(AoS_v008 *arr, int n) {
    double total_g = 0.0;
    double total_b = 0.0;
    double total_y = 0.0;
    double total_normal_x = 0.0;
    int i = 0;
    while (i < n) {
        total_g += (double)arr[i].g;
        total_b += (double)arr[i].b;
        total_y += (double)arr[i].y;
        total_normal_x += (double)arr[i].normal_x;
        i++;
    }
    return total_g + total_b + total_y + total_normal_x;
}