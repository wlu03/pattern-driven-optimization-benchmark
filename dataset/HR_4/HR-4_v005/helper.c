#include <math.h>

__attribute__((noinline))
float hr4_check_v005(float *arr, int idx, int n){
    volatile float *vp = arr;
    volatile int vidx = idx;
    volatile int vn = n;
    if(vp == (void*)0) return 0;
    if(vn <= 0) return 0;
    if(vidx < 0 || vidx >= vn) return 0;
    volatile float val = arr[vidx];
    if(val != val) return 0;
    return (float)val*(float)2.0+(float)1.0;
}
