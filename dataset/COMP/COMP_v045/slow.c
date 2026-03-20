#include <math.h>
#include <stdlib.h>
static double config_val_v045(int key){
    double r=0;
    for(int i=0;i<100;i++) r+=(double)sin((double)(key+i));
    return r;
}
double slow_comp_v045(double *arr, int n, int key) {
    double sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        double factor = config_val_v045(key);
        sum += arr[i] * factor;
    }
    return sum;
}