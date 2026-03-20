#include <math.h>
#include <stdint.h>

__attribute__((noinline))
float hr4_check_v009(float *A, float *B, int idx, int n){
    /* Defensive check 1: NULL pointers */
    volatile float *vA = A;
    volatile float *vB = B;
    if(vA == (void*)0 || vB == (void*)0) return 0;
    /* Defensive check 2: size validity */
    volatile int vn = n;
    if(vn <= 0) return 0;
    /* Defensive check 3: lower bound */
    volatile int vidx = idx;
    if(vidx < 0) return 0;
    /* Defensive check 4: upper bound (fresh volatile reads) */
    volatile int vn2 = n;
    volatile int vidx2 = idx;
    if(vidx2 >= vn2) return 0;
    /* Defensive check 5: pointer alignment */
    volatile uintptr_t addrA = (uintptr_t)A;
    volatile uintptr_t addrB = (uintptr_t)B;
    if(addrA % sizeof(float) != 0) return 0;
    if(addrB % sizeof(float) != 0) return 0;
    /* Defensive check 6: read values through volatile */
    volatile float a = A[vidx];
    volatile float b = B[vidx];
    /* Defensive check 7: NaN checks */
    volatile float a2 = a;
    volatile float b2 = b;
    if(a2 != a2 || b2 != b2) return 0;
    /* Defensive check 8: infinity checks */
    volatile float a3 = a;
    volatile float b3 = b;
    if(a3 > (float)1e30f || a3 < (float)-1e30f) return 0;
    if(b3 > (float)1e30f || b3 < (float)-1e30f) return 0;
    /* Defensive check 9: re-validate index */
    volatile int vidx3 = idx;
    volatile int vn3 = n;
    if(vidx3 >= vn3) return 0;
    return (float)(a * b);
}
