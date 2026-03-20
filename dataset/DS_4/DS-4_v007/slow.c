#ifndef AOS_V007_DEFINED
#define AOS_V007_DEFINED
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
} AoS_v007;
#endif

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_a = 0.0;
    double total_x = 0.0;
    double total_y = 0.0;
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_a += (double)arr[i].a;
        total_x += (double)arr[i].x;
        total_y += (double)arr[i].y;
        total_g += (double)arr[i].g;
    }
    return total_a + total_x + total_y + total_g;
}