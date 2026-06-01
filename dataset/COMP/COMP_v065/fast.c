#include <math.h>
#include <stdlib.h>
static __attribute__((noinline)) double config_val_v065(int key){
    volatile int _k=key; /* block ipa-pure-const inference */
    double r=0;
    for(int i=0;i<100;i++) r+=(double)sin((double)(_k+i));
    return r;
}
double fast_comp_v065(double *arr, int n, int key) {
    if (arr == NULL || n <= 0) return 0;
    double factor = config_val_v065(key);
    double sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}