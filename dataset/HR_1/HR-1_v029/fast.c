#include <math.h>
__attribute__((noinline))
void fast_hr1_v029(float *out, float *A, float *B, float *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = ((((float)sqrt(A[i] * A[i] + B[i] * B[i])) - C[i]) * A[i]) + A[i];
    }
}