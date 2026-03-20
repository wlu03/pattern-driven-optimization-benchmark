#include <math.h>

__attribute__((noinline))
float hr4_check_v000(float *A, float *B, int idx, int n){
    volatile float *vA = A;
    volatile float *vB = B;
    volatile int vidx = idx;
    volatile int vn = n;
    if(vA == (void*)0 || vB == (void*)0) return 0;
    if(vidx < 0 || vidx >= vn) return 0;
    volatile float a = A[vidx];
    volatile float b = B[vidx];
    if(a != a || b != b) return 0;
    return (float)(a * b);
}
