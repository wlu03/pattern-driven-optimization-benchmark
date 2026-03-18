#include <math.h>
__attribute__((noinline))
float config_val_v014(int key);

float slow_comp_v014(float *arr, int n, int key) {
    float sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        float factor = config_val_v014(key);
        sum += arr[i] * factor;
    }
    return sum;
}
float config_val_v014(int key) {
    float r = 0;
    for (int i = 0; i < 100; i++) r += (float)sin((double)(key+i));
    return r;
}