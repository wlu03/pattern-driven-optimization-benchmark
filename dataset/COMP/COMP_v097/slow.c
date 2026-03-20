#include <math.h>
#include <stdlib.h>
static int config_val_v097(int key){
    int r=0;
    for(int i=0;i<100;i++) r+=(int)sin((double)(key+i));
    return r;
}
int slow_comp_v097(int *arr, int n, int key) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        int factor = config_val_v097(key);
        sum += arr[i] * factor;
    }
    return sum;
}