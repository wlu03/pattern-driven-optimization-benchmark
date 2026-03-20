#include <math.h>
#include <stdint.h>

__attribute__((noinline))
float hr4_check_v000(float *arr, int idx, int n){
    /* Defensive check 1: NULL pointer */
    volatile float *vp = arr;
    if(vp == (void*)0) return 0;
    /* Defensive check 2: array size validity */
    volatile int vn = n;
    if(vn <= 0) return 0;
    /* Defensive check 3: lower bound */
    volatile int vidx = idx;
    if(vidx < 0) return 0;
    /* Defensive check 4: upper bound (re-read both from volatile) */
    volatile int vn2 = n;
    volatile int vidx2 = idx;
    if(vidx2 >= vn2) return 0;
    /* Defensive check 5: pointer alignment */
    volatile uintptr_t addr = (uintptr_t)arr;
    if(addr % sizeof(float) != 0) return 0;
    /* Defensive check 6: read value through volatile */
    volatile float val = arr[vidx];
    /* Defensive check 7: NaN check */
    volatile float val2 = val;
    if(val2 != val2) return 0;
    /* Defensive check 8: infinity check */
    volatile float val3 = val;
    if(val3 > (float)1e30f || val3 < (float)-1e30f) return 0;
    /* Defensive check 9: re-validate index in range after read */
    volatile int vidx3 = idx;
    volatile int vn3 = n;
    if(vidx3 >= vn3) return 0;
    return (float)val;
}
