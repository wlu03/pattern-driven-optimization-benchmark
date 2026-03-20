#ifndef AOS_V002_DEFINED
#define AOS_V002_DEFINED
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v002;
#endif

double slow_ds4_v002(AoS_v002 *arr, int n) {
    double total_y = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
    }
    return total_y;
}