#ifndef AOS_V015_DEFINED
#define AOS_V015_DEFINED
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
} AoS_v015;
#endif

double slow_ds4_v015(AoS_v015 *arr, int n) {
    double total_b = 0.0;
    int i = 0;
    while (i < n) {
        total_b += (double)arr[i].b;
        i++;
    }
    return total_b;
}