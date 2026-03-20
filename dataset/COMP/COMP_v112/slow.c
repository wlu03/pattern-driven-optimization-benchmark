#include <math.h>
#include <stdlib.h>
static float config_val_v112(int key){
    float r=0;
    for(int i=0;i<100;i++) r+=(float)sin((double)(key+i));
    return r;
}
float slow_comp_v112(float *arr, int n, int key) {
    float sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        float factor = config_val_v112(key);
        sum += arr[i] * factor;
    }
    return sum;
}