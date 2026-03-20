#include <math.h>

__attribute__((noinline))
double hr4_check_v002(double *arr, int idx, int n){
    volatile double *vp = arr;
    volatile int vidx = idx;
    volatile int vn = n;
    if(vp == (void*)0) return 0;
    if(vn <= 0) return 0;
    if(vidx < 0 || vidx >= vn) return 0;
    volatile double val = arr[vidx];
    if(val != val) return 0;
    return (double)val*(double)2.0+(double)1.0;
}
