#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) int config_val_v043(int key){
    volatile int _k=key; /* block ipa-pure-const inference */
    int r=0;
    for(int i=0;i<100;i++) r+=(int)sin((double)(_k+i));
    return r;
}
int slow_comp_v043(int *arr, int n, int key) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        int factor = config_val_v043(key);
        sum += arr[i] * factor;
    }
    return sum;
}