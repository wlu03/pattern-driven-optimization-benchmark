#include <math.h>
__attribute__((noinline))
void fast_hr1_v021(float *out, float *A, float *B, float *C, float *D, int n) {
    int i = 0;
    while (i < n) {
        out[i] = ((float)sqrt(A[i] * A[i] + B[i] * B[i])) + A[i];
        i++;
    }
}