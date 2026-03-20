#include <math.h>
#include <stdlib.h>
static double config_val_v114(int key){
    double r=0;
    for(int i=0;i<100;i++) r+=(double)sin((double)(key+i));
    return r;
}
double fast_comp_v114(double *arr, int n, int key) {
    if (arr == NULL || n <= 0) return 0;
    double factor = config_val_v114(key);
    double sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}