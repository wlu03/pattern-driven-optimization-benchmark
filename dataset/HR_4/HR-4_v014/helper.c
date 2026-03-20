#include <math.h>

__attribute__((noinline))
double hr4_check_v014(double *A, double *B, int idx, int n){
    volatile double *vA = A;
    volatile double *vB = B;
    volatile int vidx = idx;
    volatile int vn = n;
    if(vA == (void*)0 || vB == (void*)0) return 0;
    if(vidx < 0 || vidx >= vn) return 0;
    volatile double a = A[vidx];
    volatile double b = B[vidx];
    if(a != a || b != b) return 0;
    return (double)(a * b);
}
