#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) float config_val_v318(int key){
    volatile int _k=key; /* block ipa-pure-const inference */
    float r=0;
    for(int i=0;i<100;i++) r+=(float)sin((double)(_k+i));
    return r;
}
float slow_comp_v318(float *arr, int n, int key) {
    float sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        float factor = config_val_v318(key);
        sum += arr[i] * factor;
    }
    return sum;
}