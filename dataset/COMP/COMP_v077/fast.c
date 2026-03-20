#include <math.h>
#include <stdlib.h>
static int config_val_v077(int key){
    int r=0;
    for(int i=0;i<100;i++) r+=(int)sin((double)(key+i));
    return r;
}
int fast_comp_v077(int *arr, int n, int key) {
    if (arr == NULL || n <= 0) return 0;
    int factor = config_val_v077(key);
    int sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}