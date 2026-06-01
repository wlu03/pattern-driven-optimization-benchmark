#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) float config_val_v671(int key){
    volatile int _k=key; /* block ipa-pure-const inference */
    float r=0;
    for(int i=0;i<100;i++) r+=(float)sin((double)(_k+i));
    return r;
}
float fast_comp_v671(float *arr, int n, int key) {
    if (arr == NULL || n <= 0) return 0;
    float factor = config_val_v671(key);
    float sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}