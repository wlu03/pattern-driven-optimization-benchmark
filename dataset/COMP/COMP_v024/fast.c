#include <math.h>
#include <stdlib.h>
static float config_val_v024(int key){
    float r=0;
    for(int i=0;i<100;i++) r+=(float)sin((double)(key+i));
    return r;
}
float fast_comp_v024(float *arr, int n, int key) {
    if (arr == NULL || n <= 0) return 0;
    float factor = config_val_v024(key);
    float sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}